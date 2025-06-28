"""
PubMed scraper using pure functional programming approach.
Uses the NCBI Entrez API to fetch autoimmune disease papers.
"""

from typing import Dict, List, Any, Optional
import time
from urllib.parse import quote_plus

from ..utils.http_utils import make_get_request, create_headers, retry_request, apply_rate_limit
from ..utils.data_utils import clean_text, extract_authors, normalize_date, clean_doi, clean_pmid
from ..models.paper import create_paper
from ..config.diseases import format_search_query


# PubMed API configuration
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_SEARCH_URL = f"{PUBMED_BASE_URL}/esearch.fcgi"
PUBMED_FETCH_URL = f"{PUBMED_BASE_URL}/efetch.fcgi"
PUBMED_SUMMARY_URL = f"{PUBMED_BASE_URL}/esummary.fcgi"

DEFAULT_RATE_LIMIT = 0.34  # NCBI allows 3 requests per second
EMAIL_REQUIRED = True


def create_pubmed_search_params(
    query: str,
    max_results: int = 1000,
    date_range: Optional[Dict[str, str]] = None,
    email: str = "researcher@example.com"
) -> Dict[str, Any]:
    """Create search parameters for PubMed API. Pure function."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": min(max_results, 10000),  # PubMed limit
        "retmode": "json",
        "tool": "AutoimmuneScraper",
        "email": email,
        "sort": "relevance"
    }
    
    if date_range:
        start_year = date_range.get("start_year")
        end_year = date_range.get("end_year")
        if start_year and end_year:
            params["mindate"] = f"{start_year}/01/01"
            params["maxdate"] = f"{end_year}/12/31"
            params["datetype"] = "pdat"
    
    return params


def create_pubmed_fetch_params(pmids: List[str], email: str = "researcher@example.com") -> Dict[str, Any]:
    """Create fetch parameters for PubMed API. Pure function."""
    return {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "tool": "AutoimmuneScraper",
        "email": email
    }


@apply_rate_limit(DEFAULT_RATE_LIMIT)
def search_pubmed_ids(
    disease_key: str,
    max_results: int = 1000,
    date_range: Optional[Dict[str, str]] = None,
    email: str = "researcher@example.com"
) -> List[str]:
    """
    Search PubMed for paper IDs related to a disease. Pure function with rate limiting.
    """
    query = format_search_query(disease_key)
    params = create_pubmed_search_params(query, max_results, date_range, email)
    headers = create_headers(accept="application/json")
    
    success, response = make_get_request(PUBMED_SEARCH_URL, headers, params)
    
    if not success:
        return []
    
    data = response.get("data", {})
    esearch_result = data.get("esearchresult", {})
    pmids = esearch_result.get("idlist", [])
    
    return pmids


def parse_pubmed_author(author_element: Dict[str, Any]) -> str:
    """Parse a single author from PubMed XML data. Pure function."""
    last_name = author_element.get("LastName", "")
    fore_name = author_element.get("ForeName", "")
    initials = author_element.get("Initials", "")
    
    if last_name and fore_name:
        return f"{fore_name} {last_name}"
    elif last_name and initials:
        return f"{initials} {last_name}"
    elif last_name:
        return last_name
    else:
        return ""


def parse_pubmed_date(date_element: Dict[str, Any]) -> Optional[str]:
    """Parse publication date from PubMed data. Pure function."""
    if not date_element:
        return None
    
    year = date_element.get("Year")
    month = date_element.get("Month", "01")
    day = date_element.get("Day", "01")
    
    if year:
        try:
            # Normalize month names to numbers
            month_map = {
                "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
            }
            if month in month_map:
                month = month_map[month]
            elif not month.isdigit():
                month = "01"
            
            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            return normalize_date(date_str)
        except:
            return f"{year}-01-01"
    
    return None


def extract_mesh_terms(mesh_list: List[Dict[str, Any]]) -> List[str]:
    """Extract MeSH terms from PubMed data. Pure function."""
    mesh_terms = []
    for mesh in mesh_list:
        descriptor_name = mesh.get("DescriptorName", {})
        if isinstance(descriptor_name, dict):
            term = descriptor_name.get("text", "")
        else:
            term = str(descriptor_name)
        
        if term:
            mesh_terms.append(clean_text(term))
    
    return mesh_terms


def parse_pubmed_paper(paper_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a single paper from PubMed XML response. Pure function."""
    medline_citation = paper_data.get("MedlineCitation", {})
    article = medline_citation.get("Article", {})
    
    # Basic information
    title = clean_text(article.get("ArticleTitle", ""))
    abstract_sections = article.get("Abstract", {}).get("AbstractText", [])
    
    # Handle abstract (can be string or list)
    if isinstance(abstract_sections, list):
        abstract_parts = []
        for section in abstract_sections:
            if isinstance(section, dict):
                text = section.get("text", "")
                label = section.get("Label", "")
                if label and text:
                    abstract_parts.append(f"{label}: {text}")
                elif text:
                    abstract_parts.append(text)
            else:
                abstract_parts.append(str(section))
        abstract = " ".join(abstract_parts)
    else:
        abstract = str(abstract_sections) if abstract_sections else ""
    
    abstract = clean_text(abstract)
    
    # Authors
    author_list = article.get("AuthorList", {}).get("Author", [])
    if not isinstance(author_list, list):
        author_list = [author_list] if author_list else []
    
    authors = [parse_pubmed_author(author) for author in author_list]
    authors = [author for author in authors if author]
    
    # Journal info
    journal = article.get("Journal", {})
    journal_title = clean_text(journal.get("Title", ""))
    
    # Publication date
    pub_date = None
    date_elements = [
        article.get("ArticleDate"),
        journal.get("JournalIssue", {}).get("PubDate"),
        medline_citation.get("DateCompleted"),
        medline_citation.get("DateRevised")
    ]
    
    for date_elem in date_elements:
        if date_elem:
            pub_date = parse_pubmed_date(date_elem)
            if pub_date:
                break
    
    # Identifiers
    pmid = clean_pmid(medline_citation.get("PMID", {}).get("text", ""))
    
    # DOI extraction
    doi = ""
    article_ids = paper_data.get("PubmedData", {}).get("ArticleIdList", {}).get("ArticleId", [])
    if not isinstance(article_ids, list):
        article_ids = [article_ids] if article_ids else []
    
    for article_id in article_ids:
        if isinstance(article_id, dict) and article_id.get("IdType") == "doi":
            doi = clean_doi(article_id.get("text", ""))
            break
    
    # MeSH terms
    mesh_headings = medline_citation.get("MeshHeadingList", {}).get("MeshHeading", [])
    if not isinstance(mesh_headings, list):
        mesh_headings = [mesh_headings] if mesh_headings else []
    
    mesh_terms = extract_mesh_terms(mesh_headings)
    
    # Keywords
    keyword_list = medline_citation.get("KeywordList", {}).get("Keyword", [])
    if not isinstance(keyword_list, list):
        keyword_list = [keyword_list] if keyword_list else []
    
    keywords = [clean_text(str(kw.get("text", "") if isinstance(kw, dict) else kw)) for kw in keyword_list]
    keywords = [kw for kw in keywords if kw]
    
    return create_paper(
        title=title,
        abstract=abstract,
        authors=authors,
        journal=journal_title,
        publication_date=pub_date,
        doi=doi,
        pmid=pmid,
        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
        keywords=keywords,
        mesh_terms=mesh_terms,
        source="pubmed"
    )


@apply_rate_limit(DEFAULT_RATE_LIMIT)
def fetch_pubmed_papers(pmids: List[str], email: str = "researcher@example.com") -> List[Dict[str, Any]]:
    """
    Fetch detailed paper information from PubMed. Pure function with rate limiting.
    """
    if not pmids:
        return []
    
    # Split large requests into chunks
    chunk_size = 200  # PubMed recommended batch size
    all_papers = []
    
    for i in range(0, len(pmids), chunk_size):
        chunk_pmids = pmids[i:i + chunk_size]
        params = create_pubmed_fetch_params(chunk_pmids, email)
        headers = create_headers(accept="application/xml")
        
        success, response = make_get_request(PUBMED_FETCH_URL, headers, params)
        
        if success:
            # Note: In real implementation, you'd need to parse XML
            # For now, we'll return mock data structure
            xml_data = response.get("data", {})
            
            # This would normally parse XML, but for functional approach:
            papers = parse_pubmed_xml_response(xml_data)
            all_papers.extend(papers)
        
        # Small delay between chunks
        if i + chunk_size < len(pmids):
            time.sleep(0.1)
    
    return all_papers


def parse_pubmed_xml_response(xml_data: Any) -> List[Dict[str, Any]]:
    """
    Parse XML response from PubMed efetch. Pure function.
    Note: This is a simplified version - real implementation would use XML parsing.
    """
    # In a real implementation, you would parse the XML here
    # For now, return empty list as placeholder
    return []


def scrape_pubmed_disease(
    disease_key: str,
    max_results: int = 1000,
    date_range: Optional[Dict[str, str]] = None,
    email: str = "researcher@example.com"
) -> List[Dict[str, Any]]:
    """
    Main function to scrape papers for a disease from PubMed. Pure function.
    """
    # Search for PMIDs
    pmids = search_pubmed_ids(disease_key, max_results, date_range, email)
    
    if not pmids:
        return []
    
    # Fetch detailed paper information
    papers = fetch_pubmed_papers(pmids, email)
    
    # Add disease relevance
    papers_with_disease = []
    for paper in papers:
        paper_with_disease = paper.copy()
        current_diseases = paper_with_disease.get("disease_relevance", [])
        if disease_key not in current_diseases:
            paper_with_disease["disease_relevance"] = current_diseases + [disease_key]
        papers_with_disease.append(paper_with_disease)
    
    return papers_with_disease


def scrape_pubmed_multiple_diseases(
    disease_keys: List[str],
    max_results_per_disease: int = 1000,
    date_range: Optional[Dict[str, str]] = None,
    email: str = "researcher@example.com"
) -> List[Dict[str, Any]]:
    """
    Scrape papers for multiple diseases from PubMed. Pure function.
    """
    all_papers = []
    
    for disease_key in disease_keys:
        papers = scrape_pubmed_disease(disease_key, max_results_per_disease, date_range, email)
        all_papers.extend(papers)
    
    return all_papers 
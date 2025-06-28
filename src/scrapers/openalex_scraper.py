"""
OpenAlex scraper using pure functional programming approach.
Uses the OpenAlex API to fetch autoimmune disease papers.
"""

from typing import Dict, List, Any, Optional
import time

from ..utils.http_utils import make_get_request, create_headers, apply_rate_limit
from ..utils.data_utils import clean_text, normalize_date, clean_doi
from ..models.paper import create_paper
from ..config.diseases import get_all_search_terms

# OpenAlex API configuration
OPENALEX_BASE_URL = "https://api.openalex.org"
WORKS_ENDPOINT = "works"
DEFAULT_RATE_LIMIT = 0.1  # OpenAlex allows 10 requests per second for polite pool


def create_openalex_params(
    query: str,
    max_results: int = 1000,
    email: Optional[str] = None
) -> Dict[str, Any]:
    """Create search parameters for OpenAlex API. Pure function."""
    params = {
        "search": query,
        "per-page": min(max_results, 200),  # OpenAlex limit
        "sort": "relevance_score:desc",
        "filter": "type:article"
    }
    
    if email:
        params["mailto"] = email
    
    return params


def build_openalex_query(disease_key: str) -> str:
    """Build query string for OpenAlex search. Pure function."""
    search_terms = get_all_search_terms(disease_key)
    # OpenAlex uses simple search syntax
    return " OR ".join(f'"{term}"' for term in search_terms)


def parse_openalex_author(author_data: Dict[str, Any]) -> str:
    """Parse author information from OpenAlex response. Pure function."""
    display_name = author_data.get("display_name", "")
    return clean_text(display_name) if display_name else ""


def parse_openalex_concept(concept_data: Dict[str, Any]) -> str:
    """Parse concept information from OpenAlex response. Pure function."""
    display_name = concept_data.get("display_name", "")
    return clean_text(display_name) if display_name else ""


def parse_openalex_paper(work: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a single paper from OpenAlex API response. Pure function."""
    # Basic information
    title = clean_text(work.get("title", ""))
    
    # Abstract (OpenAlex sometimes has inverted abstract)
    abstract_inverted = work.get("abstract_inverted_index", {})
    if abstract_inverted:
        # Reconstruct abstract from inverted index
        word_positions = []
        for word, positions in abstract_inverted.items():
            for pos in positions:
                word_positions.append((pos, word))
        
        word_positions.sort(key=lambda x: x[0])
        abstract = " ".join([word for _, word in word_positions])
    else:
        abstract = ""
    
    abstract = clean_text(abstract)
    
    # Authors
    authorships = work.get("authorships", [])
    authors = []
    for authorship in authorships:
        author = authorship.get("author", {})
        author_name = parse_openalex_author(author)
        if author_name:
            authors.append(author_name)
    
    # Journal information
    primary_location = work.get("primary_location", {})
    source = primary_location.get("source", {})
    journal_title = clean_text(source.get("display_name", ""))
    
    # Publication date
    pub_date_str = work.get("publication_date", "")
    pub_date = normalize_date(pub_date_str)
    
    # Identifiers
    doi = clean_doi(work.get("doi", "").replace("https://doi.org/", ""))
    
    # OpenAlex ID
    openalex_id = work.get("id", "")
    
    # Concepts (similar to keywords/MeSH terms)
    concepts = work.get("concepts", [])
    keywords = []
    for concept in concepts:
        concept_name = parse_openalex_concept(concept)
        if concept_name and concept.get("score", 0) > 0.3:  # Only high-confidence concepts
            keywords.append(concept_name)
    
    # URL
    url = openalex_id if openalex_id else (f"https://doi.org/{doi}" if doi else "")
    
    return create_paper(
        title=title,
        abstract=abstract,
        authors=authors,
        journal=journal_title,
        publication_date=pub_date,
        doi=doi,
        url=url,
        keywords=keywords,
        source="openalex",
        metadata={
            "openalex_id": openalex_id,
            "citation_count": work.get("cited_by_count", 0),
            "is_oa": work.get("open_access", {}).get("is_oa", False),
            "oa_url": work.get("open_access", {}).get("oa_url", "")
        }
    )


@apply_rate_limit(DEFAULT_RATE_LIMIT)
def search_openalex(
    disease_key: str,
    max_results: int = 1000,
    email: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search OpenAlex for papers related to a disease. Pure function with rate limiting."""
    query = build_openalex_query(disease_key)
    params = create_openalex_params(query, max_results, email)
    headers = create_headers(accept="application/json")
    
    url = f"{OPENALEX_BASE_URL}/{WORKS_ENDPOINT}"
    success, response = make_get_request(url, headers, params)
    
    if not success:
        return []
    
    data = response.get("data", {})
    results = data.get("results", [])
    
    if not isinstance(results, list):
        results = [results] if results else []
    
    papers = []
    for result in results:
        try:
            paper = parse_openalex_paper(result)
            if paper.get("title"):  # Basic validation
                papers.append(paper)
        except Exception:
            continue
    
    return papers


def search_openalex_paginated(
    disease_key: str,
    max_results: int = 1000,
    email: Optional[str] = None,
    max_pages: int = 10
) -> List[Dict[str, Any]]:
    """Search OpenAlex with pagination support. Pure function."""
    all_papers = []
    page = 1
    per_page = min(200, max_results)
    
    while len(all_papers) < max_results and page <= max_pages:
        query = build_openalex_query(disease_key)
        params = create_openalex_params(query, per_page, email)
        params["page"] = page
        
        headers = create_headers(accept="application/json")
        url = f"{OPENALEX_BASE_URL}/{WORKS_ENDPOINT}"
        
        success, response = make_get_request(url, headers, params)
        
        if not success:
            break
        
        data = response.get("data", {})
        results = data.get("results", [])
        meta = data.get("meta", {})
        
        if not results:
            break
        
        if not isinstance(results, list):
            results = [results]
        
        page_papers = []
        for result in results:
            try:
                paper = parse_openalex_paper(result)
                if paper.get("title"):
                    page_papers.append(paper)
            except Exception:
                continue
        
        all_papers.extend(page_papers)
        
        # Check if there are more pages
        total_pages = meta.get("page", 1)
        per_page_actual = meta.get("per_page", per_page)
        count = meta.get("count", 0)
        
        if page * per_page_actual >= count:
            break
        
        page += 1
        time.sleep(0.05)  # Small delay between pages
    
    return all_papers[:max_results]


def scrape_openalex_disease(
    disease_key: str,
    max_results: int = 1000,
    email: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Main function to scrape papers for a disease from OpenAlex. Pure function."""
    papers = search_openalex_paginated(disease_key, max_results, email)
    
    # Add disease relevance
    papers_with_disease = []
    for paper in papers:
        paper_with_disease = paper.copy()
        current_diseases = paper_with_disease.get("disease_relevance", [])
        if disease_key not in current_diseases:
            paper_with_disease["disease_relevance"] = current_diseases + [disease_key]
        papers_with_disease.append(paper_with_disease)
    
    return papers_with_disease


def scrape_openalex_multiple_diseases(
    disease_keys: List[str],
    max_results_per_disease: int = 1000,
    email: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scrape papers for multiple diseases from OpenAlex. Pure function."""
    all_papers = []
    
    for disease_key in disease_keys:
        papers = scrape_openalex_disease(disease_key, max_results_per_disease, email)
        all_papers.extend(papers)
        
        # Small delay between diseases
        if disease_key != disease_keys[-1]:
            time.sleep(0.5)
    
    return all_papers 
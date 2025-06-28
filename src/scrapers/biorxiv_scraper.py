"""
bioRxiv and medRxiv scraper using pure functional programming approach.
Uses the bioRxiv API to fetch autoimmune disease preprints.
"""

from typing import Dict, List, Any, Optional
import time
from datetime import datetime, timedelta

from ..utils.http_utils import make_get_request, create_headers, apply_rate_limit
from ..utils.data_utils import clean_text, normalize_date, clean_doi
from ..models.paper import create_paper
from ..config.diseases import get_all_search_terms

# bioRxiv API configuration
BIORXIV_BASE_URL = "https://api.biorxiv.org"
DETAILS_ENDPOINT = "details"
DEFAULT_RATE_LIMIT = 1.0  # Be conservative with bioRxiv


def create_biorxiv_params(
    server: str = "biorxiv",
    interval: str = "2019-01-01/2024-12-31",
    format_type: str = "json"
) -> Dict[str, Any]:
    """Create search parameters for bioRxiv API. Pure function."""
    return {
        "server": server,
        "interval": interval,
        "format": format_type
    }


def build_date_interval(years_back: int = 5) -> str:
    """Build date interval string for bioRxiv API. Pure function."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years_back * 365)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    return f"{start_str}/{end_str}"


def matches_disease_terms(text: str, disease_key: str) -> bool:
    """Check if text contains disease-related terms. Pure function."""
    if not text:
        return False
    
    search_terms = get_all_search_terms(disease_key)
    text_lower = text.lower()
    
    return any(term.lower() in text_lower for term in search_terms)


def parse_biorxiv_author(author_data: Dict[str, Any]) -> str:
    """Parse author information from bioRxiv response. Pure function."""
    name = author_data.get("name", "")
    return clean_text(name) if name else ""


def parse_biorxiv_paper(paper_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a single paper from bioRxiv API response. Pure function."""
    # Basic information
    title = clean_text(paper_data.get("title", ""))
    abstract = clean_text(paper_data.get("abstract", ""))
    
    # Authors
    authors_str = paper_data.get("authors", "")
    if authors_str:
        # bioRxiv returns authors as a semicolon-separated string
        author_names = [clean_text(name.strip()) for name in authors_str.split(";")]
        authors = [name for name in author_names if name]
    else:
        authors = []
    
    # Journal/Server information
    server = paper_data.get("server", "")
    journal_title = f"{server.title()}" if server else "bioRxiv/medRxiv"
    
    # Publication date
    pub_date_str = paper_data.get("date", "")
    pub_date = normalize_date(pub_date_str)
    
    # DOI
    doi = clean_doi(paper_data.get("doi", ""))
    
    # URL
    url = f"https://doi.org/{doi}" if doi else ""
    
    # Category (used as keyword)
    category = paper_data.get("category", "")
    keywords = [clean_text(category)] if category else []
    
    return create_paper(
        title=title,
        abstract=abstract,
        authors=authors,
        journal=journal_title,
        publication_date=pub_date,
        doi=doi,
        url=url,
        keywords=keywords,
        source=f"{server}_preprint" if server else "biorxiv_preprint",
        metadata={
            "server": server,
            "category": category,
            "version": paper_data.get("version", ""),
            "type": "preprint"
        }
    )


@apply_rate_limit(DEFAULT_RATE_LIMIT)
def fetch_biorxiv_papers(
    server: str = "biorxiv",
    interval: Optional[str] = None,
    years_back: int = 5
) -> List[Dict[str, Any]]:
    """Fetch papers from bioRxiv/medRxiv. Pure function with rate limiting."""
    if not interval:
        interval = build_date_interval(years_back)
    
    params = create_biorxiv_params(server, interval)
    headers = create_headers(accept="application/json")
    
    url = f"{BIORXIV_BASE_URL}/{DETAILS_ENDPOINT}/{server}/{interval}"
    success, response = make_get_request(url, headers, {})
    
    if not success:
        return []
    
    data = response.get("data", {})
    collection = data.get("collection", [])
    
    if not isinstance(collection, list):
        collection = [collection] if collection else []
    
    papers = []
    for paper_data in collection:
        try:
            paper = parse_biorxiv_paper(paper_data)
            if paper.get("title") and paper.get("abstract"):
                papers.append(paper)
        except Exception:
            continue
    
    return papers


def filter_papers_by_disease(
    papers: List[Dict[str, Any]], 
    disease_key: str
) -> List[Dict[str, Any]]:
    """Filter papers by disease relevance. Pure function."""
    filtered_papers = []
    
    for paper in papers:
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        keywords = " ".join(paper.get("keywords", []))
        
        full_text = f"{title} {abstract} {keywords}"
        
        if matches_disease_terms(full_text, disease_key):
            filtered_papers.append(paper)
    
    return filtered_papers


def scrape_biorxiv_disease(
    disease_key: str,
    years_back: int = 5,
    include_medrxiv: bool = True
) -> List[Dict[str, Any]]:
    """Main function to scrape papers for a disease from bioRxiv/medRxiv. Pure function."""
    all_papers = []
    
    # Fetch from bioRxiv
    biorxiv_papers = fetch_biorxiv_papers("biorxiv", years_back=years_back)
    filtered_biorxiv = filter_papers_by_disease(biorxiv_papers, disease_key)
    all_papers.extend(filtered_biorxiv)
    
    # Fetch from medRxiv if requested
    if include_medrxiv:
        time.sleep(1.0)  # Delay between servers
        medrxiv_papers = fetch_biorxiv_papers("medrxiv", years_back=years_back)
        filtered_medrxiv = filter_papers_by_disease(medrxiv_papers, disease_key)
        all_papers.extend(filtered_medrxiv)
    
    # Add disease relevance
    papers_with_disease = []
    for paper in all_papers:
        paper_with_disease = paper.copy()
        current_diseases = paper_with_disease.get("disease_relevance", [])
        if disease_key not in current_diseases:
            paper_with_disease["disease_relevance"] = current_diseases + [disease_key]
        papers_with_disease.append(paper_with_disease)
    
    return papers_with_disease


def scrape_biorxiv_multiple_diseases(
    disease_keys: List[str],
    years_back: int = 5,
    include_medrxiv: bool = True
) -> List[Dict[str, Any]]:
    """Scrape papers for multiple diseases from bioRxiv/medRxiv. Pure function."""
    # Fetch all papers once to avoid repeated API calls
    all_biorxiv_papers = fetch_biorxiv_papers("biorxiv", years_back=years_back)
    
    all_medrxiv_papers = []
    if include_medrxiv:
        time.sleep(1.0)
        all_medrxiv_papers = fetch_biorxiv_papers("medrxiv", years_back=years_back)
    
    all_papers = []
    
    # Filter papers for each disease
    for disease_key in disease_keys:
        # Filter bioRxiv papers
        filtered_biorxiv = filter_papers_by_disease(all_biorxiv_papers, disease_key)
        
        # Filter medRxiv papers
        filtered_medrxiv = []
        if include_medrxiv:
            filtered_medrxiv = filter_papers_by_disease(all_medrxiv_papers, disease_key)
        
        # Combine and add disease relevance
        disease_papers = filtered_biorxiv + filtered_medrxiv
        
        for paper in disease_papers:
            paper_with_disease = paper.copy()
            current_diseases = paper_with_disease.get("disease_relevance", [])
            if disease_key not in current_diseases:
                paper_with_disease["disease_relevance"] = current_diseases + [disease_key]
            all_papers.append(paper_with_disease)
    
    return all_papers 
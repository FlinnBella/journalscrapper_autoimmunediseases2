"""
Europe PMC scraper using pure functional programming approach.
Uses the Europe PMC REST API to fetch autoimmune disease papers.
"""

from typing import Dict, List, Any, Optional
import time

from ..utils.http_utils import make_get_request, create_headers, apply_rate_limit
from ..utils.data_utils import clean_text, normalize_date, clean_doi, clean_pmid
from ..models.paper import create_paper
from ..config.diseases import get_all_search_terms

# Europe PMC API configuration
EUROPE_PMC_BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"
SEARCH_ENDPOINT = "search"
DEFAULT_RATE_LIMIT = 1.0


def create_europe_pmc_params(query: str, max_results: int = 1000) -> Dict[str, Any]:
    """Create search parameters for Europe PMC API. Pure function."""
    return {
        "query": query,
        "resultType": "core",
        "pageSize": min(max_results, 1000),
        "format": "json",
        "synonym": "true",
        "sort": "relevance"
    }


def build_europe_pmc_query(disease_key: str) -> str:
    """Build query string for Europe PMC search. Pure function."""
    search_terms = get_all_search_terms(disease_key)
    quoted_terms = [f'"{term}"' for term in search_terms]
    return f"({' OR '.join(quoted_terms)})"


def parse_europe_pmc_paper(result: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a single paper from Europe PMC search result. Pure function."""
    title = clean_text(result.get("title", ""))
    abstract = clean_text(result.get("abstractText", ""))
    
    # Authors
    author_list = result.get("authorList", {}).get("author", [])
    if not isinstance(author_list, list):
        author_list = [author_list] if author_list else []
    
    authors = []
    for author in author_list:
        full_name = author.get("fullName", "")
        if full_name:
            authors.append(clean_text(full_name))
    
    # Journal information
    journal_info = result.get("journalInfo", {})
    journal_title = clean_text(journal_info.get("journal", {}).get("title", ""))
    
    # Publication date
    pub_date_str = result.get("firstPublicationDate", "")
    pub_date = normalize_date(pub_date_str)
    
    # Identifiers
    pmid = clean_pmid(result.get("pmid", ""))
    doi = clean_doi(result.get("doi", ""))
    
    # URL
    url = f"https://europepmc.org/article/MED/{pmid}" if pmid else ""
    
    return create_paper(
        title=title,
        abstract=abstract,
        authors=authors,
        journal=journal_title,
        publication_date=pub_date,
        doi=doi,
        pmid=pmid,
        url=url,
        source="europe_pmc"
    )


@apply_rate_limit(DEFAULT_RATE_LIMIT)
def search_europe_pmc(disease_key: str, max_results: int = 1000) -> List[Dict[str, Any]]:
    """Search Europe PMC for papers related to a disease. Pure function with rate limiting."""
    query = build_europe_pmc_query(disease_key)
    params = create_europe_pmc_params(query, max_results)
    headers = create_headers(accept="application/json")
    
    url = f"{EUROPE_PMC_BASE_URL}/{SEARCH_ENDPOINT}"
    success, response = make_get_request(url, headers, params)
    
    if not success:
        return []
    
    data = response.get("data", {})
    result_list = data.get("resultList", {})
    results = result_list.get("result", [])
    
    if not isinstance(results, list):
        results = [results] if results else []
    
    papers = []
    for result in results:
        try:
            paper = parse_europe_pmc_paper(result)
            if paper.get("title") and paper.get("abstract"):
                papers.append(paper)
        except Exception:
            continue
    
    return papers


def scrape_europe_pmc_disease(disease_key: str, max_results: int = 1000) -> List[Dict[str, Any]]:
    """Main function to scrape papers for a disease from Europe PMC. Pure function."""
    papers = search_europe_pmc(disease_key, max_results)
    
    # Add disease relevance
    papers_with_disease = []
    for paper in papers:
        paper_with_disease = paper.copy()
        current_diseases = paper_with_disease.get("disease_relevance", [])
        if disease_key not in current_diseases:
            paper_with_disease["disease_relevance"] = current_diseases + [disease_key]
        papers_with_disease.append(paper_with_disease)
    
    return papers_with_disease

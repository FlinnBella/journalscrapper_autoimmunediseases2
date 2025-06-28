"""
Paper data model using pure functional programming approach.
No classes - only dictionaries and pure functions.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import copy


def create_paper(
    title: str = "",
    abstract: str = "",
    authors: Optional[List[str]] = None,
    journal: str = "",
    publication_date: Optional[str] = None,
    doi: str = "",
    pmid: str = "",
    url: str = "",
    keywords: Optional[List[str]] = None,
    mesh_terms: Optional[List[str]] = None,
    source: str = "",
    disease_relevance: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a paper dictionary with default values.
    Pure function that returns an immutable-style dictionary.
    """
    return {
        "id": kwargs.get("id", ""),
        "title": title,
        "abstract": abstract,
        "authors": authors or [],
        "journal": journal,
        "publication_date": publication_date,
        "doi": doi,
        "pmid": pmid,
        "url": url,
        "keywords": keywords or [],
        "mesh_terms": mesh_terms or [],
        "source": source,
        "disease_relevance": disease_relevance or [],
        "scraped_at": kwargs.get("scraped_at", datetime.now().isoformat()),
        "metadata": kwargs.get("metadata", {})
    }


def get_paper_field(paper: Dict[str, Any], field: str) -> Any:
    """Get a field from a paper dictionary. Pure function."""
    return copy.deepcopy(paper.get(field))


def update_paper_field(paper: Dict[str, Any], field: str, value: Any) -> Dict[str, Any]:
    """Update a field in a paper dictionary, returning a new dictionary. Pure function."""
    new_paper = copy.deepcopy(paper)
    new_paper[field] = value
    return new_paper


def add_author(paper: Dict[str, Any], author: str) -> Dict[str, Any]:
    """Add an author to a paper, returning a new paper dictionary. Pure function."""
    current_authors = get_paper_field(paper, "authors") or []
    new_authors = current_authors + [author] if author not in current_authors else current_authors
    return update_paper_field(paper, "authors", new_authors)


def add_keyword(paper: Dict[str, Any], keyword: str) -> Dict[str, Any]:
    """Add a keyword to a paper, returning a new paper dictionary. Pure function."""
    current_keywords = get_paper_field(paper, "keywords") or []
    new_keywords = current_keywords + [keyword] if keyword not in current_keywords else current_keywords
    return update_paper_field(paper, "keywords", new_keywords)


def add_mesh_term(paper: Dict[str, Any], mesh_term: str) -> Dict[str, Any]:
    """Add a MeSH term to a paper, returning a new paper dictionary. Pure function."""
    current_mesh = get_paper_field(paper, "mesh_terms") or []
    new_mesh = current_mesh + [mesh_term] if mesh_term not in current_mesh else current_mesh
    return update_paper_field(paper, "mesh_terms", new_mesh)


def add_disease_relevance(paper: Dict[str, Any], disease: str) -> Dict[str, Any]:
    """Add disease relevance to a paper, returning a new paper dictionary. Pure function."""
    current_diseases = get_paper_field(paper, "disease_relevance") or []
    new_diseases = current_diseases + [disease] if disease not in current_diseases else current_diseases
    return update_paper_field(paper, "disease_relevance", new_diseases)


def get_paper_id(paper: Dict[str, Any]) -> str:
    """Get paper ID, preferring DOI, then PMID, then title hash. Pure function."""
    doi = get_paper_field(paper, "doi")
    pmid = get_paper_field(paper, "pmid")
    title = get_paper_field(paper, "title")
    
    if doi:
        return f"doi:{doi}"
    elif pmid:
        return f"pmid:{pmid}"
    elif title:
        return f"title_hash:{hash(title)}"
    else:
        return f"unknown:{hash(str(paper))}"


def is_valid_paper(paper: Dict[str, Any]) -> bool:
    """Check if a paper dictionary has minimum required fields. Pure function."""
    required_fields = ["title", "abstract"]
    return all(
        field in paper and paper[field] and len(str(paper[field]).strip()) > 0
        for field in required_fields
    )


def filter_valid_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter list to only valid papers. Pure function."""
    return [paper for paper in papers if is_valid_paper(paper)]


def get_papers_by_disease(papers: List[Dict[str, Any]], disease: str) -> List[Dict[str, Any]]:
    """Filter papers by disease relevance. Pure function."""
    return [
        paper for paper in papers 
        if disease in get_paper_field(paper, "disease_relevance")
    ]


def get_papers_by_source(papers: List[Dict[str, Any]], source: str) -> List[Dict[str, Any]]:
    """Filter papers by source. Pure function."""
    return [
        paper for paper in papers 
        if get_paper_field(paper, "source") == source
    ]


def get_papers_by_journal(papers: List[Dict[str, Any]], journal: str) -> List[Dict[str, Any]]:
    """Filter papers by journal. Pure function."""
    return [
        paper for paper in papers 
        if journal.lower() in get_paper_field(paper, "journal").lower()
    ]


def get_papers_by_date_range(
    papers: List[Dict[str, Any]], 
    start_date: str, 
    end_date: str
) -> List[Dict[str, Any]]:
    """Filter papers by publication date range. Pure function."""
    def is_in_date_range(paper: Dict[str, Any]) -> bool:
        pub_date = get_paper_field(paper, "publication_date")
        if not pub_date:
            return False
        try:
            date_obj = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
            start_obj = datetime.fromisoformat(start_date)
            end_obj = datetime.fromisoformat(end_date)
            return start_obj <= date_obj <= end_obj
        except (ValueError, TypeError):
            return False
    
    return [paper for paper in papers if is_in_date_range(paper)]


def sort_papers_by_date(
    papers: List[Dict[str, Any]], 
    descending: bool = True
) -> List[Dict[str, Any]]:
    """Sort papers by publication date. Pure function."""
    def get_sort_date(paper: Dict[str, Any]) -> datetime:
        pub_date = get_paper_field(paper, "publication_date")
        try:
            return datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
        except (ValueError, TypeError, AttributeError):
            return datetime.min if descending else datetime.max
    
    return sorted(papers, key=get_sort_date, reverse=descending)


def deduplicate_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate papers based on DOI or title. Pure function."""
    seen_identifiers = set()
    unique_papers = []
    
    for paper in papers:
        doi = get_paper_field(paper, "doi")
        title = get_paper_field(paper, "title")
        
        identifier = doi if doi else title.lower().strip()
        
        if identifier not in seen_identifiers:
            seen_identifiers.add(identifier)
            unique_papers.append(paper)
    
    return unique_papers


def create_paper_summary(paper: Dict[str, Any]) -> Dict[str, str]:
    """Create a summary dictionary of key paper information. Pure function."""
    return {
        "id": get_paper_id(paper),
        "title": get_paper_field(paper, "title")[:100] + "..." if len(get_paper_field(paper, "title")) > 100 else get_paper_field(paper, "title"),
        "journal": get_paper_field(paper, "journal"),
        "publication_date": get_paper_field(paper, "publication_date"),
        "source": get_paper_field(paper, "source"),
        "author_count": str(len(get_paper_field(paper, "authors"))),
        "disease_count": str(len(get_paper_field(paper, "disease_relevance")))
    }


def merge_papers(paper1: Dict[str, Any], paper2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two paper dictionaries, preferring non-empty values. Pure function."""
    merged = copy.deepcopy(paper1)
    
    for key, value in paper2.items():
        if key in ["authors", "keywords", "mesh_terms", "disease_relevance"]:
            # Merge lists
            existing = merged.get(key, [])
            merged[key] = list(set(existing + value))
        elif not merged.get(key) and value:
            # Use value if current field is empty
            merged[key] = value
        elif key == "metadata":
            # Merge metadata dictionaries
            merged[key] = {**merged.get(key, {}), **value}
    
    return merged 
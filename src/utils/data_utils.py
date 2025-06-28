"""
Data processing utilities using pure functional programming.
No classes - only pure functions for data transformation and validation.
"""

import json
import csv
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from functools import reduce
import re
import os


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary. Pure function."""
    return data.get(key, default)


def safe_get_nested(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """Safely get a nested value from a dictionary. Pure function."""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary. Pure function."""
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def clean_text(text: str) -> str:
    """Clean and normalize text. Pure function."""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', text.strip())
    # Remove special characters that might cause issues
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', cleaned)
    return cleaned


def normalize_date(date_str: str) -> Optional[str]:
    """Normalize date string to ISO format. Pure function."""
    if not date_str:
        return None
    
    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%B %d, %Y",
        "%d %B %Y",
        "%Y"
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.isoformat()
        except ValueError:
            continue
    
    # Try to extract year if other formats fail
    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if year_match:
        try:
            year = int(year_match.group())
            return datetime(year, 1, 1).isoformat()
        except ValueError:
            pass
    
    return None


def extract_authors(author_data: Any) -> List[str]:
    """Extract and normalize author names from various formats. Pure function."""
    if not author_data:
        return []
    
    if isinstance(author_data, str):
        # Split by common separators
        authors = re.split(r'[;,]|and\s', author_data)
        return [clean_text(author) for author in authors if clean_text(author)]
    
    if isinstance(author_data, list):
        authors = []
        for author in author_data:
            if isinstance(author, str):
                authors.append(clean_text(author))
            elif isinstance(author, dict):
                # Try common author fields
                name = (author.get('name') or 
                       author.get('full_name') or 
                       f"{author.get('first_name', '')} {author.get('last_name', '')}".strip() or
                       f"{author.get('given', '')} {author.get('family', '')}".strip())
                if name:
                    authors.append(clean_text(name))
        return authors
    
    return []


def extract_keywords(keyword_data: Any) -> List[str]:
    """Extract and normalize keywords from various formats. Pure function."""
    if not keyword_data:
        return []
    
    if isinstance(keyword_data, str):
        # Split by common separators
        keywords = re.split(r'[;,]', keyword_data)
        return [clean_text(kw) for kw in keywords if clean_text(kw)]
    
    if isinstance(keyword_data, list):
        keywords = []
        for kw in keyword_data:
            if isinstance(kw, str):
                keywords.append(clean_text(kw))
            elif isinstance(kw, dict):
                # Try common keyword fields
                text = kw.get('text') or kw.get('value') or kw.get('keyword')
                if text:
                    keywords.append(clean_text(str(text)))
        return keywords
    
    return []


def clean_doi(doi: str) -> str:
    """Clean and normalize DOI. Pure function."""
    if not doi:
        return ""
    
    # Remove common prefixes
    doi = re.sub(r'^(doi:|DOI:|https?://doi\.org/|https?://dx\.doi\.org/)', '', doi.strip())
    
    # Validate DOI format (basic check)
    if re.match(r'^10\.\d+/.+', doi):
        return doi
    
    return ""


def clean_pmid(pmid: Any) -> str:
    """Clean and normalize PMID. Pure function."""
    if not pmid:
        return ""
    
    pmid_str = str(pmid).strip()
    
    # Remove common prefixes
    pmid_str = re.sub(r'^(pmid:|PMID:)', '', pmid_str, flags=re.IGNORECASE)
    
    # Check if it's a valid PMID (numeric)
    if pmid_str.isdigit():
        return pmid_str
    
    return ""


def filter_by_date_range(
    papers: List[Dict[str, Any]], 
    start_date: str, 
    end_date: str,
    date_field: str = "publication_date"
) -> List[Dict[str, Any]]:
    """Filter papers by date range. Pure function."""
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        return papers
    
    def is_in_range(paper: Dict[str, Any]) -> bool:
        pub_date = paper.get(date_field)
        if not pub_date:
            return False
        
        normalized_date = normalize_date(pub_date)
        if not normalized_date:
            return False
        
        try:
            paper_dt = datetime.fromisoformat(normalized_date)
            return start_dt <= paper_dt <= end_dt
        except ValueError:
            return False
    
    return [paper for paper in papers if is_in_range(paper)]


def group_by_field(
    papers: List[Dict[str, Any]], 
    field: str
) -> Dict[str, List[Dict[str, Any]]]:
    """Group papers by a specific field. Pure function."""
    groups = {}
    for paper in papers:
        key = paper.get(field, "unknown")
        if key not in groups:
            groups[key] = []
        groups[key].append(paper)
    return groups


def count_by_field(papers: List[Dict[str, Any]], field: str) -> Dict[str, int]:
    """Count papers by a specific field. Pure function."""
    counts = {}
    for paper in papers:
        key = paper.get(field, "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def merge_paper_lists(paper_lists: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Merge multiple lists of papers, removing duplicates. Pure function."""
    if not paper_lists:
        return []
    
    all_papers = reduce(lambda x, y: x + y, paper_lists, [])
    
    # Remove duplicates based on DOI or title
    seen = set()
    unique_papers = []
    
    for paper in all_papers:
        doi = clean_doi(paper.get("doi", ""))
        title = clean_text(paper.get("title", "")).lower()
        
        identifier = doi if doi else title
        
        if identifier and identifier not in seen:
            seen.add(identifier)
            unique_papers.append(paper)
    
    return unique_papers


def validate_paper_data(paper: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean paper data. Pure function."""
    validated = {}
    
    # Required fields
    validated["title"] = clean_text(paper.get("title", ""))
    validated["abstract"] = clean_text(paper.get("abstract", ""))
    
    # Optional fields with cleaning
    validated["authors"] = extract_authors(paper.get("authors"))
    validated["journal"] = clean_text(paper.get("journal", ""))
    validated["doi"] = clean_doi(paper.get("doi", ""))
    validated["pmid"] = clean_pmid(paper.get("pmid", ""))
    validated["url"] = paper.get("url", "")
    validated["keywords"] = extract_keywords(paper.get("keywords"))
    validated["mesh_terms"] = extract_keywords(paper.get("mesh_terms"))
    validated["source"] = clean_text(paper.get("source", ""))
    validated["disease_relevance"] = paper.get("disease_relevance", [])
    
    # Date handling
    pub_date = normalize_date(paper.get("publication_date", ""))
    validated["publication_date"] = pub_date
    
    # Metadata
    validated["scraped_at"] = paper.get("scraped_at", datetime.now().isoformat())
    validated["metadata"] = paper.get("metadata", {})
    
    return validated


def export_to_json(data: List[Dict[str, Any]], filepath: str, indent: int = 2) -> bool:
    """Export data to JSON file. Pure function with side effect."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception:
        return False


def export_to_csv(data: List[Dict[str, Any]], filepath: str) -> bool:
    """Export data to CSV file. Pure function with side effect."""
    if not data:
        return False
    
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            for row in data:
                # Flatten lists for CSV
                csv_row = {}
                for key, value in row.items():
                    if isinstance(value, list):
                        csv_row[key] = '; '.join(str(v) for v in value)
                    else:
                        csv_row[key] = str(value) if value is not None else ''
                writer.writerow(csv_row)
        return True
    except Exception:
        return False


def calculate_statistics(papers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate basic statistics about the paper collection. Pure function."""
    if not papers:
        return {}
    
    total_papers = len(papers)
    papers_with_doi = len([p for p in papers if clean_doi(p.get("doi", ""))])
    papers_with_pmid = len([p for p in papers if clean_pmid(p.get("pmid", ""))])
    
    # Date range
    dates = [normalize_date(p.get("publication_date", "")) for p in papers]
    valid_dates = [d for d in dates if d]
    
    date_range = {}
    if valid_dates:
        sorted_dates = sorted(valid_dates)
        date_range = {
            "earliest": sorted_dates[0],
            "latest": sorted_dates[-1]
        }
    
    # Source distribution
    source_counts = count_by_field(papers, "source")
    
    # Journal distribution (top 10)
    journal_counts = count_by_field(papers, "journal")
    top_journals = dict(sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    return {
        "total_papers": total_papers,
        "papers_with_doi": papers_with_doi,
        "papers_with_pmid": papers_with_pmid,
        "coverage": {
            "doi_percentage": round((papers_with_doi / total_papers) * 100, 2),
            "pmid_percentage": round((papers_with_pmid / total_papers) * 100, 2)
        },
        "date_range": date_range,
        "sources": source_counts,
        "top_journals": top_journals
    } 
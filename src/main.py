"""
Main orchestrator for the autoimmune disease journal scraper.
Uses pure functional programming approach to coordinate all scrapers.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from functools import reduce
import json

from .config.diseases import (
    get_all_disease_keys, 
    validate_disease_keys, 
    get_disease_name,
    create_disease_summary
)
from .models.paper import deduplicate_papers, filter_valid_papers, sort_papers_by_date
from .utils.data_utils import (
    merge_paper_lists, 
    export_to_json, 
    export_to_csv, 
    calculate_statistics
)
from .scrapers.pubmed_scraper import scrape_pubmed_disease, scrape_pubmed_multiple_diseases
from .scrapers.europe_pmc_scraper import scrape_europe_pmc_disease, scrape_europe_pmc_multiple_diseases  
from .scrapers.openalex_scraper import scrape_openalex_disease, scrape_openalex_multiple_diseases
from .scrapers.biorxiv_scraper import scrape_biorxiv_disease, scrape_biorxiv_multiple_diseases


# Configuration
DEFAULT_MAX_RESULTS = 1000
DEFAULT_OUTPUT_DIR = "data"
DEFAULT_DATE_RANGE_YEARS = 5

# Available scrapers
SCRAPER_FUNCTIONS = {
    "pubmed": scrape_pubmed_disease,
    "europe_pmc": scrape_europe_pmc_disease,
    "openalex": scrape_openalex_disease,
    "biorxiv": scrape_biorxiv_disease,
    # Note: Springer Nature and Core.ac.uk would require API keys
    # "springer": scrape_springer_disease,
    # "core": scrape_core_disease,
}

MULTI_SCRAPER_FUNCTIONS = {
    "pubmed": scrape_pubmed_multiple_diseases,
    "europe_pmc": scrape_europe_pmc_multiple_diseases,
    "openalex": scrape_openalex_multiple_diseases,
    "biorxiv": scrape_biorxiv_multiple_diseases,
}


def get_available_sources() -> List[str]:
    """Get list of available scraper sources. Pure function."""
    return list(SCRAPER_FUNCTIONS.keys())


def validate_sources(sources: List[str]) -> List[str]:
    """Validate and filter source names. Pure function."""
    available = get_available_sources()
    return [source for source in sources if source in available]


def create_output_filename(
    disease_keys: List[str], 
    sources: List[str], 
    format_type: str = "json"
) -> str:
    """Create output filename based on diseases and sources. Pure function."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if len(disease_keys) == 1:
        disease_part = disease_keys[0]
    elif len(disease_keys) <= 3:
        disease_part = "_".join(disease_keys)
    else:
        disease_part = f"{len(disease_keys)}_diseases"
    
    if len(sources) == 1:
        source_part = sources[0]
    elif len(sources) <= 3:
        source_part = "_".join(sources)
    else:
        source_part = f"{len(sources)}_sources"
    
    return f"autoimmune_papers_{disease_part}_{source_part}_{timestamp}.{format_type}"


def scrape_single_source(
    source: str,
    disease_keys: List[str],
    max_results_per_disease: int = DEFAULT_MAX_RESULTS,
    **kwargs
) -> List[Dict[str, Any]]:
    """Scrape papers from a single source for multiple diseases. Pure function."""
    if source not in MULTI_SCRAPER_FUNCTIONS:
        return []
    
    scraper_func = MULTI_SCRAPER_FUNCTIONS[source]
    
    try:
        # Add source-specific parameters
        if source == "pubmed":
            email = kwargs.get("email", "researcher@example.com")
            return scraper_func(disease_keys, max_results_per_disease, email=email)
        elif source == "openalex":
            email = kwargs.get("email")
            return scraper_func(disease_keys, max_results_per_disease, email=email)
        elif source == "biorxiv":
            years_back = kwargs.get("years_back", DEFAULT_DATE_RANGE_YEARS)
            return scraper_func(disease_keys, years_back=years_back)
        else:
            return scraper_func(disease_keys, max_results_per_disease)
    except Exception as e:
        print(f"Error scraping {source}: {e}")
        return []


def scrape_multiple_sources(
    sources: List[str],
    disease_keys: List[str],
    max_results_per_disease: int = DEFAULT_MAX_RESULTS,
    **kwargs
) -> Dict[str, List[Dict[str, Any]]]:
    """Scrape papers from multiple sources. Pure function."""
    results = {}
    
    for source in sources:
        print(f"Scraping {source}...")
        papers = scrape_single_source(source, disease_keys, max_results_per_disease, **kwargs)
        results[source] = papers
        print(f"Found {len(papers)} papers from {source}")
    
    return results


def combine_scraper_results(results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Combine results from multiple scrapers and remove duplicates. Pure function."""
    all_papers = []
    for source, papers in results.items():
        all_papers.extend(papers)
    
    # Remove duplicates and invalid papers
    valid_papers = filter_valid_papers(all_papers)
    unique_papers = deduplicate_papers(valid_papers)
    
    return unique_papers


def create_scraping_summary(
    results: Dict[str, List[Dict[str, Any]]],
    combined_papers: List[Dict[str, Any]],
    disease_keys: List[str]
) -> Dict[str, Any]:
    """Create a summary of scraping results. Pure function."""
    source_counts = {source: len(papers) for source, papers in results.items()}
    
    disease_summaries = {}
    for disease_key in disease_keys:
        disease_papers = [p for p in combined_papers if disease_key in p.get("disease_relevance", [])]
        disease_summaries[disease_key] = {
            "name": get_disease_name(disease_key),
            "paper_count": len(disease_papers),
            "summary": create_disease_summary(disease_key)
        }
    
    return {
        "total_papers": len(combined_papers),
        "papers_by_source": source_counts,
        "papers_by_disease": disease_summaries,
        "statistics": calculate_statistics(combined_papers),
        "scraped_at": datetime.now().isoformat()
    }


def save_results(
    papers: List[Dict[str, Any]],
    summary: Dict[str, Any],
    output_dir: str,
    filename_base: str,
    formats: List[str] = ["json"]
) -> Dict[str, bool]:
    """Save results in specified formats. Function with side effects."""
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    for format_type in formats:
        if format_type == "json":
            papers_file = os.path.join(output_dir, f"{filename_base}.json")
            summary_file = os.path.join(output_dir, f"{filename_base}_summary.json")
            
            papers_success = export_to_json(papers, papers_file)
            summary_success = export_to_json(summary, summary_file)
            results[format_type] = papers_success and summary_success
            
        elif format_type == "csv":
            csv_file = os.path.join(output_dir, f"{filename_base}.csv")
            results[format_type] = export_to_csv(papers, csv_file)
    
    return results


def main_scraper(
    disease_keys: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    max_results_per_disease: int = DEFAULT_MAX_RESULTS,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    output_formats: List[str] = ["json"],
    email: Optional[str] = None,
    years_back: int = DEFAULT_DATE_RANGE_YEARS
) -> Dict[str, Any]:
    """
    Main scraping function that orchestrates the entire process.
    Pure function that returns results without side effects.
    """
    # Use defaults if not provided
    if disease_keys is None:
        disease_keys = get_all_disease_keys()
    if sources is None:
        sources = get_available_sources()
    
    # Validate inputs
    valid_diseases = validate_disease_keys(disease_keys)
    valid_sources = validate_sources(sources)
    
    if not valid_diseases:
        return {"error": "No valid disease keys provided"}
    if not valid_sources:
        return {"error": "No valid sources provided"}
    
    print(f"Scraping {len(valid_diseases)} diseases from {len(valid_sources)} sources...")
    print(f"Diseases: {[get_disease_name(d) for d in valid_diseases]}")
    print(f"Sources: {valid_sources}")
    
    # Scrape from all sources
    scraper_results = scrape_multiple_sources(
        valid_sources,
        valid_diseases,
        max_results_per_disease,
        email=email,
        years_back=years_back
    )
    
    # Combine and process results
    combined_papers = combine_scraper_results(scraper_results)
    sorted_papers = sort_papers_by_date(combined_papers)
    
    # Create summary
    summary = create_scraping_summary(scraper_results, sorted_papers, valid_diseases)
    
    # Generate filename
    filename_base = create_output_filename(valid_diseases, valid_sources)
    filename_base = filename_base.rsplit('.', 1)[0]  # Remove extension
    
    # Save results
    save_results(sorted_papers, summary, output_dir, filename_base, output_formats)
    
    return {
        "papers": sorted_papers,
        "summary": summary,
        "filename": filename_base,
        "success": True
    }


def parse_command_line_args() -> argparse.Namespace:
    """Parse command line arguments. Pure function."""
    parser = argparse.ArgumentParser(
        description="Scrape autoimmune disease papers from academic journals"
    )
    
    parser.add_argument(
        "--diseases",
        nargs="+",
        choices=get_all_disease_keys() + ["all"],
        default=["all"],
        help="Disease keys to scrape (default: all)"
    )
    
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=get_available_sources() + ["all"],
        default=["all"],
        help="Sources to scrape from (default: all)"
    )
    
    parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help=f"Maximum results per disease per source (default: {DEFAULT_MAX_RESULTS})"
    )
    
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    
    parser.add_argument(
        "--output-format",
        nargs="+",
        choices=["json", "csv"],
        default=["json"],
        help="Output formats (default: json)"
    )
    
    parser.add_argument(
        "--email",
        help="Email for APIs that require it (PubMed, OpenAlex)"
    )
    
    parser.add_argument(
        "--years-back",
        type=int,
        default=DEFAULT_DATE_RANGE_YEARS,
        help=f"Years back to search (default: {DEFAULT_DATE_RANGE_YEARS})"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for command line usage."""
    args = parse_command_line_args()
    
    # Process arguments
    diseases = get_all_disease_keys() if "all" in args.diseases else args.diseases
    sources = get_available_sources() if "all" in args.sources else args.sources
    
    # Run the scraper
    result = main_scraper(
        disease_keys=diseases,
        sources=sources,
        max_results_per_disease=args.max_results,
        output_dir=args.output_dir,
        output_formats=args.output_format,
        email=args.email,
        years_back=args.years_back
    )
    
    if result.get("success"):
        print(f"\nScraping completed successfully!")
        print(f"Total papers found: {len(result['papers'])}")
        print(f"Results saved to: {args.output_dir}/{result['filename']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
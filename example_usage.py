#!/usr/bin/env python3
"""
Example usage script for the autoimmune disease journal scraper.
Demonstrates pure functional programming approach.
"""

import os
import sys
from pprint import pprint

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import main_scraper
from src.config.diseases import get_all_disease_keys, get_disease_name, create_disease_summary
from src.scrapers.openalex_scraper import scrape_openalex_disease
from src.scrapers.europe_pmc_scraper import scrape_europe_pmc_disease
from src.utils.data_utils import calculate_statistics


def example_single_disease_single_source():
    """Example: Scrape one disease from one source."""
    print("=" * 60)
    print("Example 1: Single Disease, Single Source")
    print("=" * 60)
    
    disease_key = "crohns"
    print(f"Scraping papers for: {get_disease_name(disease_key)}")
    print(f"Source: OpenAlex")
    print(f"Max results: 50")
    
    # Scrape papers using OpenAlex
    papers = scrape_openalex_disease(disease_key, max_results=50, email="researcher@example.com")
    
    print(f"\nFound {len(papers)} papers")
    
    if papers:
        print("\nFirst paper:")
        first_paper = papers[0]
        print(f"Title: {first_paper.get('title', 'N/A')}")
        print(f"Journal: {first_paper.get('journal', 'N/A')}")
        print(f"Authors: {', '.join(first_paper.get('authors', [])[:3])}...")
        print(f"Publication Date: {first_paper.get('publication_date', 'N/A')}")
        print(f"DOI: {first_paper.get('doi', 'N/A')}")
    
    return papers


def example_multiple_diseases_single_source():
    """Example: Scrape multiple diseases from one source."""
    print("\n" + "=" * 60)
    print("Example 2: Multiple Diseases, Single Source")
    print("=" * 60)
    
    disease_keys = ["crohns", "systemic_lupus"]
    print(f"Scraping papers for:")
    for key in disease_keys:
        print(f"  - {get_disease_name(key)}")
    print(f"Source: Europe PMC")
    print(f"Max results per disease: 25")
    
    # Scrape papers using Europe PMC
    all_papers = []
    for disease_key in disease_keys:
        papers = scrape_europe_pmc_disease(disease_key, max_results=25)
        all_papers.extend(papers)
        print(f"Found {len(papers)} papers for {get_disease_name(disease_key)}")
    
    print(f"\nTotal papers found: {len(all_papers)}")
    
    # Show statistics
    if all_papers:
        stats = calculate_statistics(all_papers)
        print(f"Papers with DOI: {stats.get('papers_with_doi', 0)}")
        print(f"Date range: {stats.get('date_range', {})}")
    
    return all_papers


def example_comprehensive_search():
    """Example: Comprehensive search using the main orchestrator."""
    print("\n" + "=" * 60)
    print("Example 3: Comprehensive Search")
    print("=" * 60)
    
    print("Using main orchestrator to search multiple diseases across multiple sources")
    
    # Select subset of diseases for demo
    disease_keys = ["crohns", "multiple_sclerosis"]
    sources = ["openalex", "biorxiv"]  # Fast sources for demo
    
    print(f"Diseases: {[get_disease_name(key) for key in disease_keys]}")
    print(f"Sources: {sources}")
    print(f"Max results per disease per source: 20")
    
    # Run comprehensive search
    result = main_scraper(
        disease_keys=disease_keys,
        sources=sources,
        max_results_per_disease=20,
        output_dir="example_output",
        output_formats=["json"],
        email="researcher@example.com"
    )
    
    if result.get("success"):
        papers = result["papers"]
        summary = result["summary"]
        
        print(f"\nScraping completed successfully!")
        print(f"Total unique papers: {len(papers)}")
        print(f"Results saved to: example_output/{result['filename']}")
        
        print(f"\nSummary:")
        print(f"Papers by source: {summary['papers_by_source']}")
        
        print(f"\nPapers by disease:")
        for disease_key, info in summary['papers_by_disease'].items():
            print(f"  {info['name']}: {info['paper_count']} papers")
    else:
        print(f"Error: {result.get('error')}")
    
    return result


def example_disease_information():
    """Example: Show disease configuration information."""
    print("\n" + "=" * 60)
    print("Example 4: Disease Configuration Information")
    print("=" * 60)
    
    print("Available diseases:")
    disease_keys = get_all_disease_keys()
    
    for disease_key in disease_keys:
        summary = create_disease_summary(disease_key)
        print(f"\n{summary['name']} ({disease_key}):")
        print(f"  Search terms: {summary['search_term_count']}")
        print(f"  Synonyms: {summary['synonym_count']}")
        print(f"  MeSH terms: {summary['mesh_term_count']}")
        print(f"  ICD codes: {summary['icd_code_count']}")
        print(f"  Total searchable terms: {summary['total_search_terms']}")


def main():
    """Run all examples."""
    print("Autoimmune Disease Journal Scraper - Example Usage")
    print("Using Pure Functional Programming Approach")
    
    try:
        # Run examples
        example_disease_information()
        
        # Note: Commented out API calls to avoid hitting rate limits during demo
        # Uncomment these to run actual scraping examples
        
        # papers1 = example_single_disease_single_source()
        # papers2 = example_multiple_diseases_single_source()
        # result = example_comprehensive_search()
        
        print("\n" + "=" * 60)
        print("Examples completed! ")
        print("=" * 60)
        print("\nTo run actual scraping examples:")
        print("1. Uncomment the API calls in this script")
        print("2. Ensure you have internet connection")
        print("3. Consider API rate limits when testing")
        print("\nFor production use:")
        print("1. Use appropriate email addresses for APIs that require them")
        print("2. Implement proper error handling and logging")
        print("3. Consider running with smaller batch sizes initially")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 
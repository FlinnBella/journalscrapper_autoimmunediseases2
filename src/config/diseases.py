"""
Configuration for autoimmune diseases and their search terms.
Pure functional programming approach with immutable data structures.
"""

from typing import Dict, List, Any
from functools import reduce
from operator import add
import copy


# Immutable disease configurations using dictionaries
DISEASE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "crohns": {
        "name": "Crohn's Disease",
        "search_terms": [
            "crohn's disease",
            "crohns disease", 
            "inflammatory bowel disease",
            "IBD",
            "regional ileitis",
            "terminal ileitis"
        ],
        "mesh_terms": [
            "Crohn Disease",
            "Inflammatory Bowel Diseases",
            "Ileitis"
        ],
        "icd_codes": ["K50", "K50.0", "K50.1", "K50.8", "K50.9"],
        "synonyms": [
            "regional enteritis",
            "granulomatous colitis",
            "granulomatous enteritis"
        ]
    },
    
    "systemic_lupus": {
        "name": "Systemic Lupus Erythematosus",
        "search_terms": [
            "systemic lupus erythematosus",
            "SLE",
            "lupus erythematosus",
            "systemic lupus",
            "lupus nephritis"
        ],
        "mesh_terms": [
            "Lupus Erythematosus, Systemic",
            "Lupus Nephritis",
            "Autoimmune Diseases"
        ],
        "icd_codes": ["M32", "M32.0", "M32.1", "M32.8", "M32.9"],
        "synonyms": [
            "disseminated lupus erythematosus",
            "libman-sacks disease"
        ]
    },
    
    "multiple_sclerosis": {
        "name": "Multiple Sclerosis",
        "search_terms": [
            "multiple sclerosis",
            "MS",
            "disseminated sclerosis",
            "relapsing-remitting multiple sclerosis",
            "RRMS",
            "progressive multiple sclerosis"
        ],
        "mesh_terms": [
            "Multiple Sclerosis",
            "Multiple Sclerosis, Relapsing-Remitting",
            "Multiple Sclerosis, Chronic Progressive",
            "Demyelinating Diseases"
        ],
        "icd_codes": ["G35"],
        "synonyms": [
            "sclerosis multiplex",
            "insular sclerosis"
        ]
    },
    
    "type1_diabetes": {
        "name": "Type 1 Diabetes",
        "search_terms": [
            "type 1 diabetes",
            "type I diabetes",
            "T1D",
            "juvenile diabetes",
            "insulin-dependent diabetes",
            "IDDM",
            "autoimmune diabetes"
        ],
        "mesh_terms": [
            "Diabetes Mellitus, Type 1",
            "Diabetes Mellitus, Insulin-Dependent",
            "Autoimmune Diseases"
        ],
        "icd_codes": ["E10", "E10.0", "E10.1", "E10.2", "E10.3", "E10.4", "E10.5", "E10.6", "E10.7", "E10.8", "E10.9"],
        "synonyms": [
            "juvenile-onset diabetes",
            "brittle diabetes"
        ]
    },
    
    "rheumatoid_arthritis": {
        "name": "Rheumatoid Arthritis",
        "search_terms": [
            "rheumatoid arthritis",
            "RA",
            "rheumatoid factor",
            "anti-CCP",
            "inflammatory arthritis",
            "polyarthritis"
        ],
        "mesh_terms": [
            "Arthritis, Rheumatoid",
            "Rheumatoid Factor",
            "Autoimmune Diseases"
        ],
        "icd_codes": ["M05", "M06", "M05.0", "M05.1", "M05.2", "M05.3", "M05.8", "M05.9", "M06.0", "M06.8", "M06.9"],
        "synonyms": [
            "chronic inflammatory arthritis",
            "proliferative arthritis"
        ]
    }
}


def get_disease_config(disease_key: str) -> Dict[str, Any]:
    """Get immutable copy of disease configuration. Pure function."""
    return copy.deepcopy(DISEASE_CONFIGS.get(disease_key, {}))


def get_disease_field(disease_key: str, field: str) -> List[str]:
    """Get a specific field from disease config. Pure function."""
    config = DISEASE_CONFIGS.get(disease_key, {})
    return list(config.get(field, []))


def get_all_search_terms(disease_key: str) -> List[str]:
    """
    Get all search terms for a disease (search_terms + synonyms).
    Pure function that returns a new list.
    """
    if disease_key not in DISEASE_CONFIGS:
        return []
    
    search_terms = get_disease_field(disease_key, "search_terms")
    synonyms = get_disease_field(disease_key, "synonyms")
    return search_terms + synonyms


def get_combined_search_terms(disease_keys: List[str]) -> List[str]:
    """
    Get combined search terms for multiple diseases.
    Uses functional approach with map and reduce.
    """
    all_terms = reduce(
        add,
        map(get_all_search_terms, disease_keys),
        []
    )
    return list(set(all_terms))


def format_search_query(disease_key: str, operator: str = "OR") -> str:
    """
    Format search terms into a query string.
    Pure function that formats terms with the given operator.
    """
    terms = get_all_search_terms(disease_key)
    quoted_terms = [f'"{term}"' for term in terms]
    return f" {operator} ".join(quoted_terms)


def get_mesh_terms(disease_key: str) -> List[str]:
    """Get MeSH terms for a disease. Pure function."""
    return get_disease_field(disease_key, "mesh_terms")


def get_icd_codes(disease_key: str) -> List[str]:
    """Get ICD codes for a disease. Pure function."""
    return get_disease_field(disease_key, "icd_codes")


def get_disease_name(disease_key: str) -> str:
    """Get the formal name of a disease. Pure function."""
    config = DISEASE_CONFIGS.get(disease_key, {})
    return config.get("name", "")


def get_search_terms(disease_key: str) -> List[str]:
    """Get primary search terms for a disease. Pure function."""
    return get_disease_field(disease_key, "search_terms")


def get_synonyms(disease_key: str) -> List[str]:
    """Get synonyms for a disease. Pure function."""
    return get_disease_field(disease_key, "synonyms")


# Functional utilities
def validate_disease_keys(disease_keys: List[str]) -> List[str]:
    """Filter to only valid disease keys. Pure function."""
    return [key for key in disease_keys if key in DISEASE_CONFIGS]


def get_all_disease_keys() -> List[str]:
    """Get all available disease keys. Pure function."""
    return list(DISEASE_CONFIGS.keys())


def is_valid_disease_key(disease_key: str) -> bool:
    """Check if a disease key is valid. Pure function."""
    return disease_key in DISEASE_CONFIGS


def count_diseases() -> int:
    """Count total number of configured diseases. Pure function."""
    return len(DISEASE_CONFIGS)


def map_disease_names(disease_keys: List[str]) -> List[str]:
    """Map disease keys to their formal names. Pure function."""
    return [get_disease_name(key) for key in validate_disease_keys(disease_keys)]


def create_disease_summary(disease_key: str) -> Dict[str, Any]:
    """Create a summary dictionary for a disease. Pure function."""
    if not is_valid_disease_key(disease_key):
        return {}
    
    return {
        "key": disease_key,
        "name": get_disease_name(disease_key),
        "search_term_count": len(get_search_terms(disease_key)),
        "synonym_count": len(get_synonyms(disease_key)),
        "mesh_term_count": len(get_mesh_terms(disease_key)),
        "icd_code_count": len(get_icd_codes(disease_key)),
        "total_search_terms": len(get_all_search_terms(disease_key))
    } 
"""
HTTP utilities using pure functional programming approach.
No classes - only pure functions for making HTTP requests.
"""

import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from functools import wraps
import json
import requests
from urllib.parse import urlencode, urlparse


def create_headers(
    user_agent: str = "AutoimmuneScraper/1.0",
    accept: str = "application/json",
    **kwargs
) -> Dict[str, str]:
    """Create HTTP headers dictionary. Pure function."""
    headers = {
        "User-Agent": user_agent,
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache"
    }
    headers.update(kwargs)
    return headers


def add_api_key_to_headers(headers: Dict[str, str], api_key: str, key_name: str = "Authorization") -> Dict[str, str]:
    """Add API key to headers dictionary. Pure function."""
    new_headers = headers.copy()
    if api_key:
        if key_name == "Authorization":
            new_headers[key_name] = f"Bearer {api_key}"
        else:
            new_headers[key_name] = api_key
    return new_headers


def build_url(base_url: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
    """Build complete URL from base, endpoint and parameters. Pure function."""
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    if params:
        url += f"?{urlencode(params)}"
    return url


def apply_rate_limit(delay_seconds: float) -> Callable:
    """Create a rate limiting decorator. Higher-order function."""
    def decorator(func: Callable) -> Callable:
        last_call_time = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            time_since_last = current_time - last_call_time[0]
            
            if time_since_last < delay_seconds:
                sleep_time = delay_seconds - time_since_last
                time.sleep(sleep_time)
            
            last_call_time[0] = time.time()
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def make_get_request(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Tuple[bool, Dict[str, Any]]:
    """
    Make a synchronous GET request. Pure function.
    Returns (success, response_data)
    """
    try:
        response = requests.get(
            url,
            headers=headers or {},
            params=params or {},
            timeout=timeout
        )
        response.raise_for_status()
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"text": response.text}
        
        return True, {
            "status_code": response.status_code,
            "data": data,
            "headers": dict(response.headers)
        }
    except Exception as e:
        return False, {
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }


def retry_request(request_func: Callable, max_retries: int = 3, backoff_factor: float = 1.0) -> Callable:
    """Add retry logic to a request function. Higher-order function."""
    def retry_wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                success, result = request_func(*args, **kwargs)
                if success:
                    return success, result
                else:
                    status_code = result.get("status_code")
                    if status_code and 400 <= status_code < 500:
                        return success, result
                    
                    if attempt < max_retries:
                        sleep_time = backoff_factor * (2 ** attempt)
                        time.sleep(sleep_time)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    sleep_time = backoff_factor * (2 ** attempt)
                    time.sleep(sleep_time)
        
        return False, {
            "error": f"Max retries exceeded. Last error: {last_exception}",
            "status_code": None
        }
    
    return retry_wrapper

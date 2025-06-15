"""
Utility functions for PC Jewellers scraper.
"""

import re
import requests
from urllib.robotparser import RobotFileParser
from typing import Optional, Dict, List
import logging


def check_robots_txt(base_url: str) -> Dict[str, bool]:
    """
    Check robots.txt for scraping permissions.
    
    Args:
        base_url: The base URL of the website
        
    Returns:
        Dictionary with permission status
    """
    try:
        robots_url = f"{base_url}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        
        # Check common paths
        test_paths = [
            "/",
            "/rings",
            "/bracelets", 
            "/necklaces",
            "/earrings",
            "/pendants"
        ]
        
        permissions = {}
        for path in test_paths:
            permissions[path] = rp.can_fetch("*", f"{base_url}{path}")
        
        return permissions
        
    except Exception as e:
        logging.warning(f"Could not check robots.txt: {str(e)}")
        return {}


def clean_price(price_text: str) -> Optional[float]:
    """
    Extract numeric price from price text.
    
    Args:
        price_text: Raw price text from webpage
        
    Returns:
        Cleaned numeric price or None
    """
    if not price_text:
        return None
    
    # Remove currency symbols and extra spaces
    cleaned = re.sub(r'[^\d.,]', '', price_text.replace(',', ''))
    
    try:
        # Handle different decimal separators
        if '.' in cleaned:
            return float(cleaned)
        else:
            return float(cleaned)
    except (ValueError, TypeError):
        return None


def clean_product_name(name: str) -> str:
    """
    Clean and normalize product names.
    
    Args:
        name: Raw product name
        
    Returns:
        Cleaned product name
    """
    if not name:
        return ""
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', name.strip())
    
    # Remove common unwanted prefixes/suffixes
    unwanted_patterns = [
        r'^(new|sale|offer)\s*[-:]?\s*',
        r'\s*[-:]\s*(new|sale|offer)$'
    ]
    
    for pattern in unwanted_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    return cleaned.strip()


def validate_url(url: str) -> bool:
    """
    Validate if URL is properly formed.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None


def get_image_info(img_url: str) -> Dict[str, str]:
    """
    Get information about an image URL.
    
    Args:
        img_url: Image URL
        
    Returns:
        Dictionary with image information
    """
    if not img_url or not validate_url(img_url):
        return {"status": "invalid", "size": "unknown", "type": "unknown"}
    
    try:
        response = requests.head(img_url, timeout=10)
        
        return {
            "status": "valid" if response.status_code == 200 else "invalid",
            "size": response.headers.get('content-length', 'unknown'),
            "type": response.headers.get('content-type', 'unknown')
        }
    except:
        return {"status": "unreachable", "size": "unknown", "type": "unknown"}


def categorize_jewelry_type(product_name: str) -> str:
    """
    Attempt to categorize jewelry based on product name.
    
    Args:
        product_name: Product name to analyze
        
    Returns:
        Jewelry category
    """
    name_lower = product_name.lower()
    
    jewelry_keywords = {
        "ring": ["ring", "band", "engagement", "wedding"],
        "necklace": ["necklace", "chain", "choker", "collar"],
        "bracelet": ["bracelet", "bangle", "cuff", "wristband"],
        "earring": ["earring", "stud", "hoop", "drop", "dangle"],
        "pendant": ["pendant", "locket", "charm"],
        "watch": ["watch", "timepiece"],
        "brooch": ["brooch", "pin"],
        "anklet": ["anklet", "ankle"]
    }
    
    for category, keywords in jewelry_keywords.items():
        if any(keyword in name_lower for keyword in keywords):
            return category
    
    return "other"


def estimate_scraping_time(num_categories: int, products_per_category: int, delay_per_request: float) -> str:
    """
    Estimate total scraping time.
    
    Args:
        num_categories: Number of categories to scrape
        products_per_category: Average products per category
        delay_per_request: Delay between requests in seconds
        
    Returns:
        Estimated time as string
    """
    total_requests = num_categories * products_per_category
    total_seconds = total_requests * delay_per_request
    
    # Add overhead for navigation, loading, etc.
    total_seconds *= 1.5
    
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Trim length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized.strip('_')

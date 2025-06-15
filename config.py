# Configuration for PC Jewellers Scraper

import os
from typing import List, Dict

# Base configuration
BASE_URL = "https://www.pcjeweller.com"
OUTPUT_DIR = "data"
LOG_DIR = "logs"

# Scraping configuration
SCRAPING_CONFIG = {
    "delay_between_requests": 1.0,  # seconds
    "delay_between_categories": 2.0,  # seconds
    "max_products_per_category": 30,  # Aim for ~150 total products (30 per category)
    "timeout": 30000,  # milliseconds
    "max_retries": 3,
    "headless": True,  # Set to False for debugging
}

# Categories to scrape
CATEGORIES = [
    {
        "name": "rings",
        "url": "/rings",
        "selector": "a[href*='/rings']"
    },
    {
        "name": "bracelets", 
        "url": "/bracelets",
        "selector": "a[href*='/bracelets']"
    },
    {
        "name": "necklaces",
        "url": "/necklaces", 
        "selector": "a[href*='/necklaces']"
    },
    {
        "name": "earrings",
        "url": "/earrings",
        "selector": "a[href*='/earrings']"
    },
    {
        "name": "pendants",
        "url": "/pendants",
        "selector": "a[href*='/pendants']"
    }
]

# Selectors for product data (will need to be adjusted based on actual site structure)
SELECTORS = {
    "product_container": ".product-item, .product-card, [data-product]",
    "product_name": ".product-name, .product-title, h3, h4",
    "product_price": ".price, .product-price, .cost",
    "product_image": "img",
    "product_link": "a",
    "load_more_button": ".load-more, .show-more, button[data-load]",
    "pagination_next": ".next, .pagination-next, button[data-next]"
}

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

# Output configuration
OUTPUT_CONFIG = {
    "save_csv": True,
    "save_json": True,
    "include_timestamp": True,
    "compress_output": False
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_logging": True
}

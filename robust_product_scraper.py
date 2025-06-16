import json
import os
import time
import random
import csv
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import cloudscraper
import httpx
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import pandas as pd
from PIL import Image
import io
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Product:
    """Product data structure"""
    name: str = ""
    price: str = ""
    original_price: str = ""
    discount: str = ""
    weight: str = ""
    metal: str = ""
    purity: str = ""
    stone: str = ""
    size: str = ""
    color: str = ""
    brand: str = ""
    category: str = ""
    subcategory: str = ""
    description: str = ""
    specifications: str = ""
    availability: str = ""
    sku: str = ""
    product_url: str = ""
    image_urls: List[str] = None
    image_files: List[str] = None

    def __post_init__(self):
        if self.image_urls is None:
            self.image_urls = []
        if self.image_files is None:
            self.image_files = []

class RobustScraper:
    def __init__(self, max_products_per_category=150):
        self.max_products_per_category = max_products_per_category
        self.base_url = "https://www.pcjeweller.com"
        self.session = None
        self.cloudscraper_session = None
        self.ua = UserAgent()
        self.products = []
        self.failed_urls = []
        self.scraped_count = 0
        self.setup_directories()
        self.setup_sessions()
        
    def setup_directories(self):
        """Create necessary directories"""
        self.base_dir = Path("scraped_data")
        self.images_dir = self.base_dir / "images"
        self.csv_dir = self.base_dir / "csv"
        
        for directory in [self.base_dir, self.images_dir, self.csv_dir]:
            directory.mkdir(exist_ok=True)
            
    def setup_sessions(self):
        """Setup multiple session types for different scraping approaches"""
        # Regular requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # CloudScraper session (bypasses Cloudflare)
        self.cloudscraper_session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'linux',
                'desktop': True
            }
        )
        
    def get_headers(self):
        """Generate realistic headers"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
    
    def fetch_page(self, url: str, method='cloudscraper') -> Optional[BeautifulSoup]:
        """Fetch page with multiple fallback methods"""
        methods = ['cloudscraper', 'requests', 'httpx']
        if method in methods:
            methods = [method] + [m for m in methods if m != method]
        
        for method_name in methods:
            try:
                if method_name == 'cloudscraper':
                    response = self.cloudscraper_session.get(url, timeout=30)
                elif method_name == 'requests':
                    response = self.session.get(url, headers=self.get_headers(), timeout=30)
                elif method_name == 'httpx':
                    with httpx.Client(headers=self.get_headers(), timeout=30) as client:
                        response = client.get(url)
                
                if response.status_code == 200:
                    logger.info(f"✓ Successfully fetched {url} using {method_name}")
                    return BeautifulSoup(response.content, 'html.parser')
                else:
                    logger.warning(f"✗ Failed to fetch {url} using {method_name}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"✗ Error fetching {url} with {method_name}: {str(e)}")
                
            # Random delay between attempts
            time.sleep(random.uniform(1, 3))
        
        return None
    
    def extract_category_from_url(self, url: str) -> str:
        """Extract category from URL"""
        try:
            path = urlparse(url).path
            if '/jewellery/' in path:
                category = path.split('/jewellery/')[-1].split('.html')[0].split('/')[0]
                return category.replace('-', ' ').title()
            return "Unknown"
        except:
            return "Unknown"
    
    def get_product_links(self, category_url: str, max_products=150) -> List[str]:
        """Extract product links from category page"""
        soup = self.fetch_page(category_url)
        if not soup:
            return []
        
        product_links = []
        
        # Common selectors for product links
        selectors = [
            'a[href*="/product/"]',
            'a[href*="/jewellery/"] img',
            '.product-item a',
            '.product-link',
            'a[href*=".html"][href*="product"]',
            'a[href*=".html"] img[src*="product"]'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    if href.startswith('/'):
                        href = urljoin(self.base_url, href)
                    if href not in product_links and 'product' in href.lower():
                        product_links.append(href)
                        if len(product_links) >= max_products:
                            break
            if len(product_links) >= max_products:
                break
        
        # Try pagination to get more products
        if len(product_links) < max_products:
            pagination_links = soup.select('a[href*="page"]')
            for page_link in pagination_links[:5]:  # Check first 5 pages
                page_href = page_link.get('href')
                if page_href:
                    if page_href.startswith('/'):
                        page_href = urljoin(self.base_url, page_href)
                    
                    page_soup = self.fetch_page(page_href)
                    if page_soup:
                        for selector in selectors:
                            links = page_soup.select(selector)
                            for link in links:
                                href = link.get('href')
                                if href:
                                    if href.startswith('/'):
                                        href = urljoin(self.base_url, href)
                                    if href not in product_links and 'product' in href.lower():
                                        product_links.append(href)
                                        if len(product_links) >= max_products:
                                            break
                            if len(product_links) >= max_products:
                                break
                    if len(product_links) >= max_products:
                        break
        
        return product_links[:max_products]
    
    def extract_product_data(self, product_url: str, category: str) -> Optional[Product]:
        """Extract product data from product page"""
        soup = self.fetch_page(product_url)
        if not soup:
            return None
        
        product = Product()
        product.product_url = product_url
        product.category = category
        
        try:
            # Extract product name
            name_selectors = [
                'h1.product-name', 'h1.product-title', '.product-name h1', 
                'h1', '.product-title', '[data-role="product-name"]'
            ]
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    product.name = name_elem.get_text(strip=True)
                    break
            
            # Extract price
            price_selectors = [
                '.price-current', '.current-price', '.price-final', 
                '.special-price', '.price .amount', '.price-box .price'
            ]
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    product.price = price_elem.get_text(strip=True)
                    break
            
            # Extract original price
            original_price_selectors = [
                '.price-old', '.old-price', '.price-was', '.regular-price'
            ]
            for selector in original_price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    product.original_price = price_elem.get_text(strip=True)
                    break
            
            # Extract specifications
            spec_data = {}
            
            # Try table format
            spec_tables = soup.select('table.product-specs, .product-attributes table, .specifications table')
            for table in spec_tables:
                rows = table.select('tr')
                for row in rows:
                    cells = row.select('td, th')
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        spec_data[key] = value
            
            # Try list format
            spec_lists = soup.select('.product-specs li, .specifications li, .product-attributes li')
            for item in spec_lists:
                text = item.get_text(strip=True)
                if ':' in text:
                    key, value = text.split(':', 1)
                    spec_data[key.strip().lower()] = value.strip()
            
            # Try div format
            spec_divs = soup.select('.spec-item, .attribute-item, .product-detail-item')
            for item in spec_divs:
                label = item.select_one('.label, .key, .name')
                value = item.select_one('.value, .val, .content')
                if label and value:
                    spec_data[label.get_text(strip=True).lower()] = value.get_text(strip=True)
            
            # Map specifications to product fields
            product.weight = spec_data.get('weight', '') or spec_data.get('gross weight', '')
            product.metal = spec_data.get('metal', '') or spec_data.get('metal type', '')
            product.purity = spec_data.get('purity', '') or spec_data.get('gold purity', '')
            product.stone = spec_data.get('stone', '') or spec_data.get('gemstone', '')
            product.size = spec_data.get('size', '') or spec_data.get('ring size', '')
            product.color = spec_data.get('color', '') or spec_data.get('metal color', '')
            product.sku = spec_data.get('sku', '') or spec_data.get('product code', '')
            
            # Extract description
            desc_selectors = [
                '.product-description', '.product-details', '.description', 
                '.product-info', '.product-summary'
            ]
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    product.description = desc_elem.get_text(strip=True)[:500]  # Limit description
                    break
            
            # Extract image URLs
            img_selectors = [
                '.product-image img', '.product-gallery img', '.product-photos img',
                '.main-image img', '.gallery-image img', 'img[src*="product"]'
            ]
            for selector in img_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        if src.startswith('/'):
                            src = urljoin(self.base_url, src)
                        if src not in product.image_urls:
                            product.image_urls.append(src)
            
            # Extract availability
            availability_selectors = [
                '.availability', '.stock-status', '.in-stock', '.out-of-stock'
            ]
            for selector in availability_selectors:
                avail_elem = soup.select_one(selector)
                if avail_elem:
                    product.availability = avail_elem.get_text(strip=True)
                    break
            
            # Set brand
            product.brand = "PC Jeweller"
            
            # Set subcategory
            breadcrumbs = soup.select('.breadcrumb a, .breadcrumbs a')
            if breadcrumbs:
                product.subcategory = breadcrumbs[-1].get_text(strip=True)
            
            logger.info(f"✓ Extracted product: {product.name[:50]}...")
            return product
            
        except Exception as e:
            logger.error(f"✗ Error extracting product data from {product_url}: {str(e)}")
            return None
    
    def download_image(self, image_url: str, category: str, product_name: str, img_index: int) -> Optional[str]:
        """Download and save product image"""
        try:
            # Create category directory
            category_dir = self.images_dir / category.replace(' ', '_').lower()
            category_dir.mkdir(exist_ok=True)
            
            # Generate filename
            safe_name = re.sub(r'[^\w\s-]', '', product_name.lower()[:30])
            safe_name = re.sub(r'[-\s]+', '-', safe_name)
            
            # Get file extension
            parsed_url = urlparse(image_url)
            ext = parsed_url.path.split('.')[-1] if '.' in parsed_url.path else 'jpg'
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                ext = 'jpg'
            
            filename = f"{safe_name}_{img_index}.{ext}"
            filepath = category_dir / filename
            
            # Download image
            response = self.session.get(image_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save image
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✓ Downloaded image: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"✗ Error downloading image {image_url}: {str(e)}")
            return None
    
    def process_product(self, product_url: str, category: str) -> Optional[Product]:
        """Process a single product - extract data and download images"""
        product = self.extract_product_data(product_url, category)
        if not product:
            return None
        
        # Download images
        for i, img_url in enumerate(product.image_urls[:5]):  # Limit to 5 images per product
            filepath = self.download_image(img_url, category, product.name, i)
            if filepath:
                product.image_files.append(filepath)
            
            # Small delay between image downloads
            time.sleep(0.5)
        
        return product
    
    def scrape_category(self, category_url: str) -> List[Product]:
        """Scrape all products from a category"""
        category = self.extract_category_from_url(category_url)
        logger.info(f"🔍 Scraping category: {category} from {category_url}")
        
        # Get product links
        product_links = self.get_product_links(category_url, self.max_products_per_category)
        logger.info(f"📦 Found {len(product_links)} product links in {category}")
        
        if not product_links:
            logger.warning(f"⚠️ No product links found for category: {category}")
            return []
        
        # Process products with threading
        category_products = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.process_product, url, category): url 
                for url in product_links
            }
            
            for future in as_completed(futures):
                try:
                    product = future.result()
                    if product:
                        category_products.append(product)
                        self.scraped_count += 1
                        logger.info(f"✅ Scraped product {self.scraped_count}: {product.name[:50]}...")
                    else:
                        self.failed_urls.append(futures[future])
                except Exception as e:
                    logger.error(f"❌ Error processing product: {str(e)}")
                    self.failed_urls.append(futures[future])
                
                # Random delay between products
                time.sleep(random.uniform(0.5, 2))
        
        logger.info(f"✅ Completed scraping {category}: {len(category_products)} products")
        return category_products
    
    def save_to_csv(self, products: List[Product], filename: str = "products.csv"):
        """Save products to CSV file"""
        filepath = self.csv_dir / filename
        
        if not products:
            logger.warning("No products to save")
            return
        
        # Convert products to dictionaries
        products_data = []
        for product in products:
            data = asdict(product)
            data['image_urls'] = '; '.join(data['image_urls'])
            data['image_files'] = '; '.join(data['image_files'])
            products_data.append(data)
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(products_data)
        df.to_csv(filepath, index=False, encoding='utf-8')
        logger.info(f"💾 Saved {len(products)} products to {filepath}")
    
    def run(self, links_file: str = "pcjeweller_links.json"):
        """Main scraping function"""
        logger.info("🚀 Starting PC Jeweller Product Scraper")
        
        # Load links
        try:
            with open(links_file, 'r', encoding='utf-8') as f:
                links_data = json.load(f)
        except Exception as e:
            logger.error(f"❌ Error loading links file: {str(e)}")
            return
        
        # Filter jewelry category links
        jewelry_links = []
        for link_data in links_data:
            url = link_data['url']
            if '/jewellery/' in url and url.endswith('.html'):
                jewelry_links.append(url)
        
        logger.info(f"📋 Found {len(jewelry_links)} jewelry category links")
        
        # Scrape each category
        for i, category_url in enumerate(jewelry_links):
            logger.info(f"🔄 Processing category {i+1}/{len(jewelry_links)}: {category_url}")
            
            category_products = self.scrape_category(category_url)
            self.products.extend(category_products)
            
            # Save progress periodically
            if (i + 1) % 5 == 0:
                self.save_to_csv(self.products, f"products_progress_{i+1}.csv")
            
            # Longer delay between categories
            time.sleep(random.uniform(3, 7))
        
        # Final save
        self.save_to_csv(self.products, "final_products.csv")
        
        # Save failed URLs
        if self.failed_urls:
            with open(self.csv_dir / "failed_urls.txt", 'w') as f:
                for url in self.failed_urls:
                    f.write(f"{url}\n")
        
        logger.info(f"🎉 Scraping completed!")
        logger.info(f"📊 Total products scraped: {len(self.products)}")
        logger.info(f"❌ Failed URLs: {len(self.failed_urls)}")

if __name__ == "__main__":
    # Create and run scraper
    scraper = RobustScraper(max_products_per_category=150)
    scraper.run("pcjeweller_links.json")

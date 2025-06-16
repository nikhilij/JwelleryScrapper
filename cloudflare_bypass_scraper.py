#!/usr/bin/env python3

import requests
import json
import csv
import os
import time
import random
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pathlib import Path
import logging
from fake_useragent import UserAgent
import cloudscraper
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CloudflareBypasser:
    """Advanced Cloudflare bypass using multiple techniques"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = None
        self.cloudscraper_session = None
        self.success_count = 0
        self.fail_count = 0
        self.setup_sessions()
    
    def setup_sessions(self):
        """Setup multiple session types"""
        try:
            # CloudScraper - specialized for Cloudflare bypass
            self.cloudscraper_session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'linux',
                    'desktop': True
                },
                delay=10  # Wait for challenge completion
            )
            logger.info("✅ CloudScraper session initialized")
            
            # Regular requests session with advanced headers
            self.session = requests.Session()
            self.session.headers.update(self.get_advanced_headers())
            
        except Exception as e:
            logger.error(f"❌ Error setting up sessions: {e}")
    
    def get_advanced_headers(self):
        """Generate advanced headers to mimic real browser"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
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
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"'
        }
    
    def fetch_page(self, url, method='cloudscraper', retries=3):
        """Fetch page with advanced bypass techniques"""
        
        for attempt in range(retries):
            try:
                logger.info(f"🔍 Attempt {attempt + 1}: Fetching {url}")
                
                if method == 'cloudscraper':
                    # Use CloudScraper for Cloudflare bypass
                    response = self.cloudscraper_session.get(
                        url, 
                        timeout=30,
                        allow_redirects=True
                    )
                else:
                    # Use regular requests with rotating headers
                    headers = self.get_advanced_headers()
                    response = self.session.get(
                        url,
                        headers=headers,
                        timeout=30,
                        allow_redirects=True
                    )
                
                # Check response
                if response.status_code == 200:
                    # Verify we got actual content, not a challenge page
                    content = response.text.lower()
                    if any(keyword in content for keyword in ['jewellery', 'jewelry', 'ring', 'necklace', 'product']):
                        self.success_count += 1
                        logger.info(f"✅ SUCCESS: {url} (method: {method})")
                        return BeautifulSoup(response.content, 'html.parser')
                    else:
                        logger.warning(f"⚠️  Got challenge/block page for {url}")
                
                elif response.status_code == 403:
                    logger.warning(f"⚠️  403 Forbidden: {url}")
                    
                elif response.status_code == 429:
                    logger.warning(f"⚠️  Rate limited: {url}")
                    time.sleep(30)  # Wait longer for rate limit
                    
                else:
                    logger.warning(f"⚠️  Status {response.status_code}: {url}")
                
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Timeout for {url}")
                
            except Exception as e:
                logger.error(f"❌ Error fetching {url}: {str(e)}")
            
            # Wait before retry
            wait_time = random.uniform(5, 15) * (attempt + 1)
            logger.info(f"⏳ Waiting {wait_time:.1f}s before retry...")
            time.sleep(wait_time)
        
        self.fail_count += 1
        logger.error(f"❌ FAILED after {retries} attempts: {url}")
        return None

class ProductScraper:
    """Main product scraping class"""
    
    def __init__(self, max_products_per_category=150):
        self.bypasser = CloudflareBypasser()
        self.max_products = max_products_per_category
        self.products = []
        self.failed_urls = []
        self.images_downloaded = 0
        self.setup_directories()
        
    def setup_directories(self):
        """Create output directories"""
        self.base_dir = Path("scraped_data")
        self.images_dir = self.base_dir / "images"
        self.csv_dir = self.base_dir / "csv"
        self.json_dir = self.base_dir / "json"
        
        for directory in [self.base_dir, self.images_dir, self.csv_dir, self.json_dir]:
            directory.mkdir(exist_ok=True)
            
        logger.info("📁 Created output directories")
    
    def extract_category_name(self, url):
        """Extract category name from URL"""
        try:
            path = urlparse(url).path
            if '/jewellery/' in path:
                category = path.split('/jewellery/')[-1].split('.html')[0].split('/')[-1]
                return category.replace('-', ' ').title()
            return "Unknown"
        except:
            return "Unknown"
    
    def get_product_links(self, category_url):
        """Extract product links from category page"""
        soup = self.bypasser.fetch_page(category_url)
        if not soup:
            return []
        
        product_links = set()
        
        # Multiple selectors to find product links
        selectors = [
            'a[href*="product-"]',
            'a[href*="/product/"]',
            '.product-item a',
            '.item a',
            'a[href*=".html"] img',
            '[class*="product"] a',
            'a[href*="jewellery"] img'
        ]
        
        for selector in selectors:
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        # Convert to absolute URL
                        if href.startswith('/'):
                            href = urljoin("https://www.pcjeweller.com", href)
                        
                        # Filter for product URLs
                        if any(keyword in href.lower() for keyword in ['product', 'jewellery', 'jewelry']):
                            product_links.add(href)
                            
                        if len(product_links) >= self.max_products:
                            break
                            
            except Exception as e:
                logger.warning(f"⚠️  Error with selector {selector}: {e}")
                continue
        
        # Try pagination for more products
        try:
            pagination_links = soup.select('a[href*="page"], .pagination a, .pager a')
            for page_link in pagination_links[:3]:  # Check first 3 pages only
                page_href = page_link.get('href')
                if page_href and page_href not in [category_url]:
                    if page_href.startswith('/'):
                        page_href = urljoin("https://www.pcjeweller.com", page_href)
                    
                    logger.info(f"🔍 Checking pagination: {page_href}")
                    page_soup = self.bypasser.fetch_page(page_href)
                    if page_soup:
                        for selector in selectors[:3]:  # Use fewer selectors for speed
                            page_links = page_soup.select(selector)
                            for link in page_links:
                                href = link.get('href')
                                if href:
                                    if href.startswith('/'):
                                        href = urljoin("https://www.pcjeweller.com", href)
                                    if any(keyword in href.lower() for keyword in ['product', 'jewellery']):
                                        product_links.add(href)
                                        if len(product_links) >= self.max_products:
                                            break
                    
                    if len(product_links) >= self.max_products:
                        break
                        
        except Exception as e:
            logger.warning(f"⚠️  Error processing pagination: {e}")
        
        result = list(product_links)[:self.max_products]
        logger.info(f"📦 Found {len(result)} product links")
        return result
    
    def extract_product_data(self, product_url, category):
        """Extract data from individual product page"""
        soup = self.bypasser.fetch_page(product_url)
        if not soup:
            return None
        
        product = {
            'name': '',
            'price': '',
            'original_price': '',
            'discount': '',
            'weight': '',
            'metal': '',
            'purity': '',
            'stone': '',
            'size': '',
            'color': '',
            'brand': 'PC Jeweller',
            'category': category,
            'subcategory': '',
            'description': '',
            'specifications': '',
            'availability': '',
            'sku': '',
            'product_url': product_url,
            'image_urls': []
        }
        
        try:
            # Extract product name
            name_selectors = [
                'h1.product-name', 'h1.product-title', '.product-name h1',
                'h1', '.product-title', '[data-role="product-name"]',
                '.product-info h1', '.item-name h1'
            ]
            for selector in name_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    product['name'] = elem.get_text(strip=True)
                    break
            
            # Extract price information
            price_selectors = [
                '.price-current', '.current-price', '.price-final',
                '.special-price', '.price .amount', '.price-box .price',
                '[class*="current-price"]', '[class*="special-price"]'
            ]
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product['price'] = elem.get_text(strip=True)
                    break
            
            # Extract original price
            original_price_selectors = [
                '.price-old', '.old-price', '.price-was', '.regular-price',
                '[class*="old-price"]', '[class*="regular-price"]'
            ]
            for selector in original_price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product['original_price'] = elem.get_text(strip=True)
                    break
            
            # Extract specifications
            spec_data = {}
            
            # Try different specification formats
            spec_containers = soup.select('table.product-specs, .product-attributes, .specifications, .product-details')
            for container in spec_containers:
                rows = container.select('tr, .spec-row, .attribute-row')
                for row in rows:
                    cells = row.select('td, .spec-label, .spec-value')
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            spec_data[key] = value
            
            # Try list format
            spec_lists = soup.select('.product-specs li, .specifications li, .attributes li')
            for item in spec_lists:
                text = item.get_text(strip=True)
                if ':' in text:
                    parts = text.split(':', 1)
                    if len(parts) == 2:
                        key, value = parts
                        spec_data[key.strip().lower()] = value.strip()
            
            # Map specifications to product fields
            for key, value in spec_data.items():
                if any(w in key for w in ['weight', 'gross weight', 'net weight']):
                    product['weight'] = value
                elif any(w in key for w in ['metal', 'metal type', 'material']):
                    product['metal'] = value
                elif any(w in key for w in ['purity', 'gold purity', 'karat']):
                    product['purity'] = value
                elif any(w in key for w in ['stone', 'gemstone', 'diamond']):
                    product['stone'] = value
                elif any(w in key for w in ['size', 'ring size']):
                    product['size'] = value
                elif any(w in key for w in ['color', 'colour', 'metal color']):
                    product['color'] = value
                elif any(w in key for w in ['sku', 'product code', 'item code']):
                    product['sku'] = value
            
            # Extract images
            img_selectors = [
                '.product-image img', '.product-gallery img', '.product-photos img',
                '.main-image img', '.gallery-image img', 'img[src*="product"]',
                '.zoom-image img', '.product-view img'
            ]
            for selector in img_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src') or img.get('data-original')
                    if src:
                        if src.startswith('/'):
                            src = urljoin("https://www.pcjeweller.com", src)
                        if src not in product['image_urls'] and 'product' in src.lower():
                            product['image_urls'].append(src)
            
            # Extract description
            desc_selectors = [
                '.product-description', '.product-details', '.description',
                '.product-info .description', '.summary', '.product-summary'
            ]
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    desc_text = elem.get_text(strip=True)
                    if len(desc_text) > 20:  # Only if substantial content
                        product['description'] = desc_text[:500]  # Limit length
                        break
            
            # Extract availability
            availability_selectors = [
                '.availability', '.stock-status', '.in-stock', '.out-of-stock',
                '[class*="stock"]', '[class*="availability"]'
            ]
            for selector in availability_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product['availability'] = elem.get_text(strip=True)
                    break
            
            # Set specifications as JSON string
            if spec_data:
                product['specifications'] = json.dumps(spec_data)
            
            if product['name']:  # Only return if we got at least a name
                logger.info(f"✅ Extracted: {product['name'][:50]}...")
                return product
            else:
                logger.warning(f"⚠️  No product name found for {product_url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error extracting product data from {product_url}: {str(e)}")
            return None
    
    def download_image(self, image_url, category, product_name, img_index):
        """Download product image"""
        try:
            # Create category directory
            category_safe = "".join(c for c in category if c.isalnum() or c in (' ', '-', '_')).rstrip()
            category_dir = self.images_dir / category_safe.replace(' ', '_').lower()
            category_dir.mkdir(exist_ok=True)
            
            # Generate safe filename
            name_safe = "".join(c for c in product_name[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            name_safe = name_safe.replace(' ', '_')
            
            # Get file extension
            ext = 'jpg'
            if '.' in image_url:
                ext = image_url.split('.')[-1].split('?')[0].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                    ext = 'jpg'
            
            filename = f"{name_safe}_{img_index}.{ext}"
            filepath = category_dir / filename
            
            # Download with timeout
            response = requests.get(image_url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.images_downloaded += 1
                logger.info(f"📷 Downloaded image {self.images_downloaded}: {filename}")
                return str(filepath)
            else:
                logger.warning(f"⚠️  Failed to download image: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error downloading image {image_url}: {str(e)}")
            
        return None
    
    def scrape_category(self, category_url):
        """Scrape all products from a category"""
        category = self.extract_category_name(category_url)
        logger.info(f"\n🔍 SCRAPING CATEGORY: {category}")
        logger.info(f"📄 URL: {category_url}")
        
        # Get product links
        product_links = self.get_product_links(category_url)
        if not product_links:
            logger.warning(f"⚠️  No product links found for {category}")
            return []
        
        logger.info(f"📦 Processing {len(product_links)} products...")
        
        category_products = []
        
        # Process products one by one
        for i, product_url in enumerate(product_links):
            logger.info(f"\n📦 Product {i+1}/{len(product_links)}: {product_url}")
            
            # Extract product data
            product = self.extract_product_data(product_url, category)
            if product:
                # Download images (limit to 3 per product)
                for j, img_url in enumerate(product['image_urls'][:3]):
                    filepath = self.download_image(img_url, category, product['name'], j)
                    time.sleep(1)  # Small delay between image downloads
                
                category_products.append(product)
                
                # Save progress every 10 products
                if (i + 1) % 10 == 0:
                    self.save_progress(category_products, f"{category}_progress")
                    logger.info(f"💾 Saved progress: {len(category_products)} products")
            else:
                self.failed_urls.append(product_url)
            
            # Delay between products to be respectful
            delay = random.uniform(3, 8)
            logger.info(f"⏳ Waiting {delay:.1f}s...")
            time.sleep(delay)
        
        logger.info(f"✅ COMPLETED {category}: {len(category_products)} products extracted")
        return category_products
    
    def save_progress(self, products, filename):
        """Save products to CSV and JSON"""
        if not products:
            return
        
        # Save CSV
        csv_file = self.csv_dir / f"{filename}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if products:
                fieldnames = products[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for product in products:
                    # Convert image URLs list to string for CSV
                    row = product.copy()
                    row['image_urls'] = '; '.join(product['image_urls'])
                    writer.writerow(row)
        
        # Save JSON
        json_file = self.json_dir / f"{filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved to: {csv_file} and {json_file}")
    
    def run_scraper(self):
        """Main scraping execution"""
        logger.info("🚀 STARTING CLOUDFLARE BYPASS SCRAPER")
        logger.info("=" * 60)
        
        # Load categories
        try:
            with open('priority_categories.json', 'r') as f:
                categories = json.load(f)
        except FileNotFoundError:
            logger.error("❌ priority_categories.json not found")
            return
        
        logger.info(f"📋 Loaded {len(categories)} categories")
        
        all_products = []
        
        # Process each category
        for category_name, category_urls in categories.items():
            logger.info(f"\n🏷️  CATEGORY: {category_name.upper()}")
            logger.info(f"📄 URLs to process: {len(category_urls)}")
            
            # Process first 2 URLs per category (for testing - can be increased)
            for i, url in enumerate(category_urls[:2]):
                logger.info(f"\n🔄 Processing URL {i+1}/{min(2, len(category_urls))}")
                
                category_products = self.scrape_category(url)
                all_products.extend(category_products)
                
                # Longer delay between category pages
                if i < len(category_urls[:2]) - 1:
                    delay = random.uniform(10, 20)
                    logger.info(f"⏳ Waiting {delay:.1f}s before next URL...")
                    time.sleep(delay)
            
            # Delay between categories
            delay = random.uniform(15, 30)
            logger.info(f"⏳ Category completed. Waiting {delay:.1f}s before next category...")
            time.sleep(delay)
        
        # Final save
        if all_products:
            self.save_progress(all_products, "final_all_products")
            
            # Save statistics
            stats = {
                'total_products': len(all_products),
                'images_downloaded': self.images_downloaded,
                'success_rate': f"{self.bypasser.success_count}/{self.bypasser.success_count + self.bypasser.fail_count}",
                'failed_urls': len(self.failed_urls),
                'categories_processed': len(categories)
            }
            
            with open(self.json_dir / "scraping_stats.json", 'w') as f:
                json.dump(stats, f, indent=2)
            
            logger.info(f"\n🎉 SCRAPING COMPLETED!")
            logger.info(f"📊 Total products: {len(all_products)}")
            logger.info(f"📷 Images downloaded: {self.images_downloaded}")
            logger.info(f"✅ Success rate: {stats['success_rate']}")
            logger.info(f"❌ Failed URLs: {len(self.failed_urls)}")
            
        else:
            logger.warning("⚠️  No products were successfully scraped")

def main():
    print("🌩️  CLOUDFLARE BYPASS SCRAPER")
    print("=" * 40)
    print("🛡️  Uses advanced CloudScraper to bypass protection")
    print("⚡ More reliable than browser automation")
    print()
    
    choice = input("Start scraping? (y/n): ").lower().strip()
    
    if choice == 'y':
        scraper = ProductScraper(max_products_per_category=150)
        scraper.run_scraper()
    else:
        print("👋 Use manual_scraping_guide.md for the manual approach")

if __name__ == "__main__":
    main()

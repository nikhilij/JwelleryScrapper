import undetected_chromedriver as uc
import time
import json
import csv
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import random
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedAutomatedScraper:
    def __init__(self, max_products_per_category=150):
        self.max_products = max_products_per_category
        self.driver = None
        self.products = []
        self.setup_directories()
        
    def setup_directories(self):
        """Create necessary directories"""
        self.base_dir = Path("scraped_data")
        self.images_dir = self.base_dir / "images"
        self.csv_dir = self.base_dir / "csv"
        
        for directory in [self.base_dir, self.images_dir, self.csv_dir]:
            directory.mkdir(exist_ok=True)
    
    def setup_driver(self):
        """Setup undetected Chrome driver"""
        try:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # For headless operation
            options.add_argument("--headless")
            
            # Let undetected-chromedriver auto-detect the version
            self.driver = uc.Chrome(options=options)
            
            # Execute script to hide webdriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Successfully setup undetected Chrome driver")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup driver: {str(e)}")
            return False
    
    def get_page_source(self, url, wait_time=5):
        """Get page source using undetected Chrome"""
        try:
            logger.info(f"🔍 Loading: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(wait_time)
            
            # Check if page loaded successfully
            title = self.driver.title
            if "403" in title or "forbidden" in title.lower():
                logger.warning(f"⚠️  Possible block detected for: {url}")
                return None
            
            logger.info(f"✅ Successfully loaded: {title[:50]}...")
            return self.driver.page_source
            
        except Exception as e:
            logger.error(f"❌ Error loading {url}: {str(e)}")
            return None
    
    def extract_product_links(self, category_url):
        """Extract product links from category page"""
        page_source = self.get_page_source(category_url)
        if not page_source:
            return []
        
        soup = BeautifulSoup(page_source, 'html.parser')
        product_links = []
        
        # Look for product links
        selectors = [
            'a[href*="product"]',
            'a[href*=".html"] img',
            '.product-item a',
            '.item a',
            '[class*="product"] a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    if href.startswith('/'):
                        href = urljoin("https://www.pcjeweller.com", href)
                    if href not in product_links and 'product' in href.lower():
                        product_links.append(href)
                        if len(product_links) >= self.max_products:
                            break
            if len(product_links) >= self.max_products:
                break
        
        logger.info(f"📦 Found {len(product_links)} product links")
        return product_links[:self.max_products]
    
    def scrape_product_details(self, product_url, category):
        """Scrape individual product details"""
        page_source = self.get_page_source(product_url, wait_time=3)
        if not page_source:
            return None
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        product = {
            'name': '',
            'price': '',
            'original_price': '',
            'weight': '',
            'metal': '',
            'purity': '',
            'stone': '',
            'size': '',
            'color': '',
            'brand': 'PC Jeweller',
            'category': category,
            'description': '',
            'availability': '',
            'sku': '',
            'product_url': product_url,
            'image_urls': []
        }
        
        try:
            # Extract product name
            name_selectors = ['h1', '.product-name', '.product-title', '[data-role="product-name"]']
            for selector in name_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product['name'] = elem.get_text(strip=True)
                    break
            
            # Extract price
            price_selectors = ['.price-current', '.current-price', '.special-price', '.price']
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product['price'] = elem.get_text(strip=True)
                    break
            
            # Extract specifications from tables
            spec_tables = soup.select('table tr')
            for row in spec_tables:
                cells = row.select('td')
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    if 'weight' in key:
                        product['weight'] = value
                    elif 'metal' in key:
                        product['metal'] = value
                    elif 'purity' in key:
                        product['purity'] = value
                    elif 'stone' in key or 'gem' in key:
                        product['stone'] = value
                    elif 'size' in key:
                        product['size'] = value
                    elif 'color' in key:
                        product['color'] = value
                    elif 'sku' in key or 'code' in key:
                        product['sku'] = value
            
            # Extract images
            img_selectors = ['.product-image img', '.gallery img', 'img[src*="product"]']
            for selector in img_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        if src.startswith('/'):
                            src = urljoin("https://www.pcjeweller.com", src)
                        if src not in product['image_urls']:
                            product['image_urls'].append(src)
            
            # Extract description
            desc_selectors = ['.description', '.product-details', '.summary']
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product['description'] = elem.get_text(strip=True)[:500]
                    break
            
            logger.info(f"✅ Scraped: {product['name'][:50]}...")
            return product
            
        except Exception as e:
            logger.error(f"❌ Error scraping product {product_url}: {str(e)}")
            return None
    
    def download_image(self, image_url, category, product_name, img_index):
        """Download product image"""
        try:
            # Create category directory
            category_dir = self.images_dir / category.replace(' ', '_').lower()
            category_dir.mkdir(exist_ok=True)
            
            # Generate safe filename
            safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name[:30].replace(' ', '_')
            
            # Get file extension
            ext = image_url.split('.')[-1].split('?')[0] if '.' in image_url else 'jpg'
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                ext = 'jpg'
            
            filename = f"{safe_name}_{img_index}.{ext}"
            filepath = category_dir / filename
            
            # Download image
            response = requests.get(image_url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"📷 Downloaded: {filename}")
                return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Error downloading {image_url}: {str(e)}")
            return None
    
    def scrape_category(self, category_url):
        """Scrape entire category"""
        category = category_url.split('/')[-1].replace('.html', '').replace('-', ' ').title()
        logger.info(f"🔍 Scraping category: {category}")
        
        # Get product links
        product_links = self.extract_product_links(category_url)
        if not product_links:
            logger.warning(f"⚠️  No products found in {category}")
            return []
        
        category_products = []
        
        for i, product_url in enumerate(product_links):
            logger.info(f"📦 Scraping product {i+1}/{len(product_links)}")
            
            product = self.scrape_product_details(product_url, category)
            if product:
                # Download images
                for j, img_url in enumerate(product['image_urls'][:3]):  # Limit to 3 images
                    filepath = self.download_image(img_url, category, product['name'], j)
                    time.sleep(0.5)  # Small delay between image downloads
                
                category_products.append(product)
                
                # Save progress every 10 products
                if (i + 1) % 10 == 0:
                    self.save_progress(category_products, f"{category}_progress_{i+1}")
            
            # Random delay between products
            time.sleep(random.uniform(2, 5))
        
        logger.info(f"✅ Completed {category}: {len(category_products)} products")
        return category_products
    
    def save_progress(self, products, filename):
        """Save progress to CSV"""
        if not products:
            return
        
        filepath = self.csv_dir / f"{filename}.csv"
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if products:
                writer = csv.DictWriter(f, fieldnames=products[0].keys())
                writer.writeheader()
                for product in products:
                    # Convert image URLs list to string
                    product_copy = product.copy()
                    product_copy['image_urls'] = '; '.join(product['image_urls'])
                    writer.writerow(product_copy)
        
        logger.info(f"💾 Saved progress: {filepath}")
    
    def run_scraper(self):
        """Main scraping function"""
        logger.info("🚀 Starting Advanced Automated Scraper")
        
        if not self.setup_driver():
            logger.error("❌ Failed to setup driver. Exiting.")
            return
        
        try:
            # Load priority categories
            with open('priority_categories.json', 'r') as f:
                categories = json.load(f)
            
            logger.info(f"📋 Found {len(categories)} categories to scrape")
            
            all_products = []
            
            # Scrape each category
            for category_name, category_urls in categories.items():
                logger.info(f"🔄 Processing category: {category_name.upper()}")
                
                for url in category_urls[:2]:  # Limit to first 2 URLs per category for testing
                    category_products = self.scrape_category(url)
                    all_products.extend(category_products)
                    
                    # Longer delay between categories
                    time.sleep(random.uniform(5, 10))
            
            # Final save
            self.save_progress(all_products, "final_products")
            
            logger.info(f"🎉 Scraping completed! Total products: {len(all_products)}")
            
        except Exception as e:
            logger.error(f"❌ Error during scraping: {str(e)}")
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔚 Driver closed")

def main():
    print("🤖 ADVANCED AUTOMATED SCRAPER")
    print("=" * 40)
    print("⚠️  WARNING: This uses browser automation which may still be detected.")
    print("🔄 If this fails, please use the manual scraping guide instead.")
    print()
    
    choice = input("Continue with automated scraping? (y/n): ").lower().strip()
    
    if choice == 'y':
        scraper = AdvancedAutomatedScraper(max_products_per_category=150)
        scraper.run_scraper()
    else:
        print("👍 Please refer to 'manual_scraping_guide.md' for the manual approach.")

if __name__ == "__main__":
    main()

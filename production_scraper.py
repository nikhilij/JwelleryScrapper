#!/usr/bin/env python3

import cloudscraper
import time
import json
import csv
import os
import requests
import random
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pathlib import Path
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionScraper:
    """Production-ready scraper for all PC Jeweller categories"""
    
    def __init__(self, max_products_per_category=150):
        self.max_products = max_products_per_category
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'linux', 'desktop': True}
        )
        self.products = []
        self.total_scraped = 0
        self.images_downloaded = 0
        self.failed_urls = []
        self.lock = threading.Lock()
        self.setup_directories()
        
    def setup_directories(self):
        """Create output directories"""
        self.base_dir = Path("scraped_data")
        self.images_dir = self.base_dir / "images"
        self.csv_dir = self.base_dir / "csv"
        self.json_dir = self.base_dir / "json"
        self.progress_dir = self.base_dir / "progress"
        
        for directory in [self.base_dir, self.images_dir, self.csv_dir, self.json_dir, self.progress_dir]:
            directory.mkdir(exist_ok=True)
            
    def get_product_links_with_pagination(self, category_url):
        """Extract product links including pagination"""
        all_links = set()
        
        # Get first page
        page_links = self.get_product_links_from_page(category_url)
        all_links.update(page_links)
        
        # Try to find pagination and get more pages
        try:
            response = self.scraper.get(category_url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for pagination links
                pagination_selectors = [
                    '.pagination a', '.pager a', '[class*="page"] a',
                    'a[href*="page="]', 'a[href*="p="]'
                ]
                
                page_urls = set()
                for selector in pagination_selectors:
                    page_links = soup.select(selector)
                    for link in page_links:
                        href = link.get('href')
                        if href and ('page=' in href or 'p=' in href):
                            if href.startswith('/'):
                                href = urljoin("https://www.pcjeweller.com", href)
                            page_urls.add(href)
                
                # Process additional pages (limit to 5 pages for efficiency)
                for i, page_url in enumerate(list(page_urls)[:5]):
                    if len(all_links) >= self.max_products:
                        break
                        
                    logger.info(f"🔍 Processing page {i+2}: {page_url}")
                    page_links = self.get_product_links_from_page(page_url)
                    all_links.update(page_links)
                    
                    time.sleep(2)  # Delay between pages
                    
        except Exception as e:
            logger.warning(f"⚠️  Error processing pagination: {e}")
        
        result = list(all_links)[:self.max_products]
        logger.info(f"✅ Total unique product links found: {len(result)}")
        return result
    
    def get_product_links_from_page(self, page_url):
        """Extract product links from a single page"""
        try:
            response = self.scraper.get(page_url, timeout=30)
            if response.status_code != 200:
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            product_links = set()
            
            # Optimized selectors based on successful testing
            selectors = [
                '.productListing a[href*=".html"]',
                '.pdt-item-list a[href*=".html"]',
                'a[href*="-ring-"], a[href*="-necklace-"], a[href*="-earring-"], a[href*="-bracelet-"], a[href*="-pendant-"], a[href*="-chain-"]',
                'a[title="View Details"]'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href and href.endswith('.html'):
                        if href.startswith('/'):
                            href = urljoin("https://www.pcjeweller.com", href)
                        
                        # Clean URL (remove query parameters)
                        clean_href = href.split('?')[0]
                        
                        # Filter for actual product pages
                        if any(keyword in clean_href.lower() for keyword in ['-ring-', '-necklace-', '-earring-', '-bracelet-', '-pendant-', '-chain-', '-bangle-']):
                            product_links.add(clean_href)
            
            return list(product_links)
            
        except Exception as e:
            logger.error(f"❌ Error extracting links from {page_url}: {str(e)}")
            return []
    
    def extract_product_details(self, product_url, category):
        """Extract comprehensive product details"""
        try:
            response = self.scraper.get(product_url, timeout=30)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
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
            
            # Extract product name
            name_selectors = [
                'h1.product-name', 'h1', '.product-title',
                '.pdt-name', '[class*="product-name"]', '.item-name'
            ]
            for selector in name_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    product['name'] = elem.get_text(strip=True)
                    break
            
            # Extract pricing information
            price_container = soup.select_one('.price-container, .product-price, .pdt-price')\n            if price_container:\n                # Look for current price\n                current_price = price_container.select_one('.current-price, .special-price, .discounted-price')\n                if current_price:\n                    product['price'] = current_price.get_text(strip=True)\n                \n                # Look for original price\n                original_price = price_container.select_one('.original-price, .regular-price, .mrp')\n                if original_price:\n                    product['original_price'] = original_price.get_text(strip=True)\n            \n            # Fallback price extraction\n            if not product['price']:\n                price_text = soup.get_text()\n                price_match = re.search(r'₹[\\d,]+', price_text)\n                if price_match:\n                    product['price'] = price_match.group()\n            \n            # Extract product specifications\n            specs = {}\n            \n            # Try structured specification tables\n            spec_tables = soup.select('.specifications table, .product-specs table, .details table')\n            for table in spec_tables:\n                rows = table.select('tr')\n                for row in rows:\n                    cells = row.select('td, th')\n                    if len(cells) >= 2:\n                        key = cells[0].get_text(strip=True).lower()\n                        value = cells[1].get_text(strip=True)\n                        if key and value:\n                            specs[key] = value\n            \n            # Try definition lists\n            dl_elements = soup.select('.specifications dl, .product-details dl')\n            for dl in dl_elements:\n                dts = dl.select('dt')\n                dds = dl.select('dd')\n                for dt, dd in zip(dts, dds):\n                    key = dt.get_text(strip=True).lower()\n                    value = dd.get_text(strip=True)\n                    if key and value:\n                        specs[key] = value\n            \n            # Try list items with colons\n            spec_lists = soup.select('.specifications li, .product-details li, .specs li')\n            for item in spec_lists:\n                text = item.get_text(strip=True)\n                if ':' in text:\n                    parts = text.split(':', 1)\n                    if len(parts) == 2:\n                        key, value = parts\n                        specs[key.strip().lower()] = value.strip()\n            \n            # Map specifications to product fields\n            for key, value in specs.items():\n                if any(w in key for w in ['weight', 'gross weight', 'net weight']):\n                    product['weight'] = value\n                elif any(w in key for w in ['metal', 'metal type', 'material']):\n                    product['metal'] = value\n                elif any(w in key for w in ['purity', 'gold purity', 'karat', 'kt']):\n                    product['purity'] = value\n                elif any(w in key for w in ['stone', 'gemstone', 'diamond', 'gem']):\n                    product['stone'] = value\n                elif any(w in key for w in ['size', 'ring size']):\n                    product['size'] = value\n                elif any(w in key for w in ['color', 'colour', 'metal color']):\n                    product['color'] = value\n                elif any(w in key for w in ['sku', 'product code', 'item code', 'model']):\n                    product['sku'] = value\n            \n            # Extract images\n            img_selectors = [\n                '.product-image img', '.pdt-image img', '.gallery img',\n                '.product-gallery img', '.zoom-image img',\n                'img[src*=\"catalog/product\"]', 'img[alt*=\"Ring\"], img[alt*=\"Necklace\"]'\n            ]\n            \n            for selector in img_selectors:\n                images = soup.select(selector)\n                for img in images:\n                    src = img.get('src') or img.get('data-src') or img.get('data-original')\n                    if src:\n                        if src.startswith('//'):\n                            src = 'https:' + src\n                        elif src.startswith('/'):\n                            src = urljoin("https://www.pcjeweller.com", src)\n                        \n                        if src not in product['image_urls'] and 'catalog/product' in src:\n                            product['image_urls'].append(src)\n            \n            # Extract description\n            desc_selectors = [\n                '.product-description', '.description', '.pdt-description',\n                '.product-details .description', '.summary', '.product-summary'\n            ]\n            for selector in desc_selectors:\n                elem = soup.select_one(selector)\n                if elem:\n                    desc_text = elem.get_text(strip=True)\n                    if len(desc_text) > 20:\n                        product['description'] = desc_text[:400]  # Limit length\n                        break\n            \n            # Calculate discount if both prices available\n            if product['price'] and product['original_price']:\n                try:\n                    current = float(re.sub(r'[^\\d.]', '', product['price']))\n                    original = float(re.sub(r'[^\\d.]', '', product['original_price']))\n                    if original > current:\n                        discount = round(((original - current) / original) * 100, 1)\n                        product['discount'] = f\"{discount}%\"\n                except:\n                    pass\n            \n            # Extract availability\n            availability_selectors = [\n                '.availability', '.stock-status', '.in-stock', '.out-of-stock',\n                '[class*=\"stock\"]', '[class*=\"availability\"]'\n            ]\n            for selector in availability_selectors:\n                elem = soup.select_one(selector)\n                if elem:\n                    product['availability'] = elem.get_text(strip=True)\n                    break\n            \n            # Set specifications as JSON string\n            if specs:\n                product['specifications'] = json.dumps(specs)\n            \n            # Extract subcategory from breadcrumbs\n            breadcrumbs = soup.select('.breadcrumb a, .breadcrumbs a')\n            if len(breadcrumbs) > 1:\n                product['subcategory'] = breadcrumbs[-1].get_text(strip=True)\n            \n            if product['name']:  # Only return if we got essential data\n                with self.lock:\n                    self.total_scraped += 1\n                logger.info(f\"✅ [{self.total_scraped}] {product['name'][:50]}... - {product['price']}\")\n                return product\n            else:\n                return None\n                \n        except Exception as e:\n            logger.error(f\"❌ Error extracting product from {product_url}: {str(e)}\")\n            return None\n    \n    def download_image(self, image_url, category, product_name, img_index):\n        \"\"\"Download product image with error handling\"\"\"\n        try:\n            # Create safe paths\n            category_safe = re.sub(r'[^\\w\\s-]', '', category).strip()\n            category_dir = self.images_dir / category_safe.replace(' ', '_').lower()\n            category_dir.mkdir(exist_ok=True)\n            \n            name_safe = re.sub(r'[^\\w\\s-]', '', product_name[:30]).strip()\n            name_safe = name_safe.replace(' ', '_')\n            \n            # Get file extension\n            ext = 'jpg'\n            if '.' in image_url:\n                ext = image_url.split('.')[-1].split('?')[0].lower()\n                if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:\n                    ext = 'jpg'\n            \n            filename = f\"{name_safe}_{img_index}.{ext}\"\n            filepath = category_dir / filename\n            \n            # Skip if file already exists\n            if filepath.exists():\n                return str(filepath)\n            \n            # Download with proper headers\n            headers = {\n                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',\n                'Referer': 'https://www.pcjeweller.com/'\n            }\n            \n            response = requests.get(image_url, stream=True, timeout=20, headers=headers)\n            if response.status_code == 200:\n                with open(filepath, 'wb') as f:\n                    for chunk in response.iter_content(chunk_size=8192):\n                        f.write(chunk)\n                \n                with self.lock:\n                    self.images_downloaded += 1\n                    \n                if self.images_downloaded % 50 == 0:\n                    logger.info(f\"📷 Downloaded {self.images_downloaded} images so far...\")\n                    \n                return str(filepath)\n                \n        except Exception as e:\n            logger.warning(f\"⚠️  Error downloading image {image_url}: {str(e)}\")\n            \n        return None\n    \n    def scrape_category(self, category_name, category_urls):\n        \"\"\"Scrape all URLs in a category\"\"\"\n        logger.info(f\"\\n🏷️  SCRAPING CATEGORY: {category_name.upper()}\")\n        logger.info(f\"📄 Processing {len(category_urls)} URLs\")\n        \n        category_products = []\n        \n        for i, category_url in enumerate(category_urls):\n            logger.info(f\"\\n🔄 URL {i+1}/{len(category_urls)}: {category_url}\")\n            \n            # Get product links with pagination\n            product_links = self.get_product_links_with_pagination(category_url)\n            if not product_links:\n                logger.warning(f\"⚠️  No products found at {category_url}\")\n                continue\n            \n            # Process products\n            url_products = []\n            for j, product_url in enumerate(product_links):\n                if len(category_products) >= self.max_products:\n                    logger.info(f\"✅ Reached maximum products ({self.max_products}) for {category_name}\")\n                    break\n                    \n                product = self.extract_product_details(product_url, category_name)\n                if product:\n                    # Download images (limit to 3 per product)\n                    for k, img_url in enumerate(product['image_urls'][:3]):\n                        self.download_image(img_url, category_name, product['name'], k)\n                        time.sleep(0.3)  # Small delay between images\n                    \n                    url_products.append(product)\n                    category_products.append(product)\n                else:\n                    self.failed_urls.append(product_url)\n                \n                # Respectful delay between products\n                time.sleep(random.uniform(1, 3))\n            \n            # Save progress for this URL\n            if url_products:\n                self.save_progress(url_products, f\"{category_name}_url_{i+1}\")\n            \n            # Break if we have enough products\n            if len(category_products) >= self.max_products:\n                break\n                \n            # Delay between URLs\n            time.sleep(random.uniform(5, 10))\n        \n        logger.info(f\"✅ {category_name.upper()} COMPLETED: {len(category_products)} products\")\n        return category_products\n    \n    def save_progress(self, products, filename):\n        \"\"\"Save progress to CSV and JSON\"\"\"\n        if not products:\n            return\n        \n        # Save CSV\n        csv_file = self.progress_dir / f\"{filename}.csv\"\n        with open(csv_file, 'w', newline='', encoding='utf-8') as f:\n            if products:\n                fieldnames = products[0].keys()\n                writer = csv.DictWriter(f, fieldnames=fieldnames)\n                writer.writeheader()\n                \n                for product in products:\n                    row = product.copy()\n                    row['image_urls'] = '; '.join(product['image_urls'])\n                    writer.writerow(row)\n        \n        # Save JSON\n        json_file = self.progress_dir / f\"{filename}.json\"\n        with open(json_file, 'w', encoding='utf-8') as f:\n            json.dump(products, f, indent=2, ensure_ascii=False)\n    \n    def save_final_results(self, all_products):\n        \"\"\"Save final consolidated results\"\"\"\n        if not all_products:\n            logger.warning(\"⚠️  No products to save\")\n            return\n        \n        # Save comprehensive CSV\n        csv_file = self.csv_dir / \"all_products_final.csv\"\n        with open(csv_file, 'w', newline='', encoding='utf-8') as f:\n            fieldnames = all_products[0].keys()\n            writer = csv.DictWriter(f, fieldnames=fieldnames)\n            writer.writeheader()\n            \n            for product in all_products:\n                row = product.copy()\n                row['image_urls'] = '; '.join(product['image_urls'])\n                writer.writerow(row)\n        \n        # Save JSON\n        json_file = self.json_dir / \"all_products_final.json\"\n        with open(json_file, 'w', encoding='utf-8') as f:\n            json.dump(all_products, f, indent=2, ensure_ascii=False)\n        \n        # Save by category\n        by_category = {}\n        for product in all_products:\n            category = product['category']\n            if category not in by_category:\n                by_category[category] = []\n            by_category[category].append(product)\n        \n        for category, products in by_category.items():\n            cat_csv = self.csv_dir / f\"{category.lower()}_products.csv\"\n            with open(cat_csv, 'w', newline='', encoding='utf-8') as f:\n                fieldnames = products[0].keys()\n                writer = csv.DictWriter(f, fieldnames=fieldnames)\n                writer.writeheader()\n                \n                for product in products:\n                    row = product.copy()\n                    row['image_urls'] = '; '.join(product['image_urls'])\n                    writer.writerow(row)\n        \n        # Save statistics\n        stats = {\n            'total_products': len(all_products),\n            'images_downloaded': self.images_downloaded,\n            'failed_urls': len(self.failed_urls),\n            'categories': list(by_category.keys()),\n            'products_by_category': {cat: len(prods) for cat, prods in by_category.items()},\n            'scraping_completed': time.strftime('%Y-%m-%d %H:%M:%S')\n        }\n        \n        with open(self.json_dir / \"scraping_statistics.json\", 'w') as f:\n            json.dump(stats, f, indent=2)\n        \n        logger.info(f\"💾 Final results saved:\")\n        logger.info(f\"   📊 {csv_file}\")\n        logger.info(f\"   📊 {json_file}\")\n        logger.info(f\"   📊 Category-wise CSV files\")\n        logger.info(f\"   📊 Statistics file\")\n    \n    def run_production_scraping(self):\n        \"\"\"Main production scraping execution\"\"\"\n        logger.info(\"🚀 STARTING PRODUCTION SCRAPING\")\n        logger.info(\"=\" * 60)\n        \n        # Load categories\n        try:\n            with open('priority_categories.json', 'r') as f:\n                categories = json.load(f)\n        except FileNotFoundError:\n            logger.error(\"❌ priority_categories.json not found\")\n            return\n        \n        logger.info(f\"📋 Loaded {len(categories)} categories\")\n        logger.info(f\"🎯 Target: {self.max_products} products per category\")\n        \n        all_products = []\n        \n        # Process each category\n        for category_name, category_urls in categories.items():\n            logger.info(f\"\\n{'='*60}\")\n            logger.info(f\"🔄 PROCESSING: {category_name.upper()}\")\n            logger.info(f\"📄 URLs: {len(category_urls)}\")\n            \n            category_products = self.scrape_category(category_name, category_urls)\n            all_products.extend(category_products)\n            \n            # Save progress after each category\n            if category_products:\n                self.save_progress(category_products, f\"category_{category_name}\")\n            \n            # Long delay between categories\n            delay = random.uniform(20, 40)\n            logger.info(f\"⏳ Category completed. Waiting {delay:.1f}s before next...\")\n            time.sleep(delay)\n        \n        # Save final results\n        self.save_final_results(all_products)\n        \n        # Save failed URLs\n        if self.failed_urls:\n            with open(self.base_dir / \"failed_urls.txt\", 'w') as f:\n                for url in self.failed_urls:\n                    f.write(f\"{url}\\n\")\n        \n        # Final summary\n        logger.info(f\"\\n🎉 PRODUCTION SCRAPING COMPLETED!\")\n        logger.info(f\"=\"*60)\n        logger.info(f\"📊 FINAL STATISTICS:\")\n        logger.info(f\"   🏆 Total products scraped: {len(all_products)}\")\n        logger.info(f\"   📷 Images downloaded: {self.images_downloaded}\")\n        logger.info(f\"   ❌ Failed URLs: {len(self.failed_urls)}\")\n        logger.info(f\"   📁 Categories processed: {len(categories)}\")\n        \n        # Category breakdown\n        by_category = {}\n        for product in all_products:\n            category = product['category']\n            by_category[category] = by_category.get(category, 0) + 1\n        \n        logger.info(f\"\\n📋 PRODUCTS BY CATEGORY:\")\n        for category, count in by_category.items():\n            logger.info(f\"   🏷️  {category}: {count} products\")\n        \n        logger.info(f\"\\n💾 Results saved to 'scraped_data/' directory\")\n        \n        return all_products\n\ndef main():\n    print(\"🏭 PC JEWELLER PRODUCTION SCRAPER\")\n    print(\"=\" * 40)\n    print(\"🎯 Comprehensive scraping of all categories\")\n    print(\"📦 150 products per category with images\")\n    print(\"💾 Organized output with progress saving\")\n    print()\n    \n    max_products = input(\"Products per category (default 150): \").strip()\n    if not max_products:\n        max_products = 150\n    else:\n        max_products = int(max_products)\n    \n    print(f\"\\n🚀 Starting production scraping with {max_products} products per category...\")\n    print(\"⏳ This will take several hours to complete.\")\n    print(\"📁 Progress will be saved continuously.\")\n    print()\n    \n    choice = input(\"Continue? (y/n): \").lower().strip()\n    \n    if choice == 'y':\n        scraper = ProductionScraper(max_products_per_category=max_products)\n        scraper.run_production_scraping()\n    else:\n        print(\"👋 Scraping cancelled\")\n\nif __name__ == \"__main__\":\n    main()\n

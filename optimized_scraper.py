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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_success.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PCJewellerScraper:
    """Optimized scraper with correct selectors"""
    
    def __init__(self, max_products_per_category=150):
        self.max_products = max_products_per_category
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'linux', 'desktop': True}
        )
        self.products = []
        self.setup_directories()
        
    def setup_directories(self):
        """Create output directories"""
        self.base_dir = Path("scraped_data")
        self.images_dir = self.base_dir / "images"
        self.csv_dir = self.base_dir / "csv"
        
        for directory in [self.base_dir, self.images_dir, self.csv_dir]:
            directory.mkdir(exist_ok=True)
            
    def get_product_links(self, category_url):
        """Extract product links using correct selectors"""
        try:
            response = self.scraper.get(category_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"❌ Failed to load {category_url}: {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            product_links = set()
            
            # Correct selectors based on page analysis
            selectors = [
                '.productListing a[href*=".html"]',  # Main product container
                '.pdt-item-list a[href*=".html"]',   # Product item list
                'a[href*="-ring-"], a[href*="-necklace-"], a[href*="-earring-"]',  # Product-specific patterns
                'a[title="View Details"]'  # View details links
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                logger.info(f"🔍 Selector '{selector}' found {len(links)} links")
                
                for link in links:
                    href = link.get('href')
                    if href and href.endswith('.html'):
                        # Convert to absolute URL
                        if href.startswith('/'):
                            href = urljoin("https://www.pcjeweller.com", href)
                        
                        # Filter out bid parameters and duplicates
                        clean_href = href.split('?')[0]  # Remove query parameters
                        
                        # Only include actual product pages
                        if any(keyword in clean_href.lower() for keyword in ['-ring-', '-necklace-', '-earring-', '-bracelet-', '-pendant-', '-chain-']):
                            product_links.add(clean_href)
                            
                        if len(product_links) >= self.max_products:
                            break
                            
                if len(product_links) >= self.max_products:
                    break
            
            result = list(product_links)[:self.max_products]
            logger.info(f"✅ Found {len(result)} unique product links")
            
            # Log sample links for verification
            for i, link in enumerate(result[:3]):
                logger.info(f"   {i+1}. {link}")
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Error extracting product links from {category_url}: {str(e)}")
            return []
    
    def extract_product_details(self, product_url, category):
        """Extract detailed product information"""
        try:
            response = self.scraper.get(product_url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"⚠️  Failed to load product page: {response.status_code}")
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
                'description': '',
                'sku': '',
                'availability': '',
                'product_url': product_url,
                'image_urls': []
            }
            
            # Extract product name
            name_selectors = [
                'h1.product-name', 'h1', '.product-title', 
                '.pdt-name', '[class*="product-name"]'
            ]
            for selector in name_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    product['name'] = elem.get_text(strip=True)
                    break
            
            # Extract price
            price_selectors = [
                '.current-price', '.price-current', '.special-price',
                '.price .amount', '[class*="price"]', '.pdt-price'
            ]
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    price_text = elem.get_text(strip=True)
                    if '₹' in price_text or 'Rs' in price_text:
                        product['price'] = price_text
                        break
            
            # Extract original price (strikethrough price)
            original_price_selectors = [
                '.price-old', '.old-price', '.regular-price',
                '.price-was', '[class*="old-price"]'
            ]
            for selector in original_price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product['original_price'] = elem.get_text(strip=True)
                    break
            
            # Extract product specifications
            spec_containers = soup.select('.product-specs, .specifications, .product-details, .pdt-specs')
            for container in spec_containers:
                # Look for table rows
                rows = container.select('tr')
                for row in rows:
                    cells = row.select('td, th')
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        if 'weight' in key:
                            product['weight'] = value
                        elif 'metal' in key:
                            product['metal'] = value
                        elif 'purity' in key or 'karat' in key:
                            product['purity'] = value
                        elif 'stone' in key or 'diamond' in key:
                            product['stone'] = value
                        elif 'size' in key:
                            product['size'] = value
                        elif 'color' in key:
                            product['color'] = value
                        elif 'sku' in key or 'code' in key:
                            product['sku'] = value
                
                # Look for list items
                items = container.select('li, .spec-item')
                for item in items:
                    text = item.get_text(strip=True)
                    if ':' in text:
                        key, value = text.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if 'weight' in key:
                            product['weight'] = value
                        elif 'metal' in key:
                            product['metal'] = value
                        elif 'purity' in key:
                            product['purity'] = value
                        elif 'stone' in key:
                            product['stone'] = value
            
            # Extract images
            img_selectors = [
                '.product-image img', '.pdt-image img', '.gallery img',
                'img[alt*="Ring"], img[alt*="Necklace"], img[alt*="Earring"]',
                'img[src*="catalog/product"]'
            ]
            for selector in img_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = urljoin("https://www.pcjeweller.com", src)
                        
                        if src not in product['image_urls'] and 'catalog/product' in src:
                            product['image_urls'].append(src)
            
            # Extract description
            desc_selectors = [
                '.product-description', '.description', '.pdt-description',
                '.product-details p', '.summary'
            ]
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    desc_text = elem.get_text(strip=True)
                    if len(desc_text) > 20:
                        product['description'] = desc_text[:300]  # Limit length
                        break
            
            # Calculate discount if both prices available
            if product['price'] and product['original_price']:
                try:
                    current = float(re.sub(r'[^\d.]', '', product['price']))
                    original = float(re.sub(r'[^\d.]', '', product['original_price']))
                    if original > current:
                        discount = round(((original - current) / original) * 100, 1)
                        product['discount'] = f"{discount}%"
                except:
                    pass
            
            if product['name']:  # Only return if we got essential data
                logger.info(f"✅ Extracted: {product['name'][:50]}... (₹{product['price']})")
                return product
            else:
                logger.warning(f"⚠️  Insufficient data extracted from {product_url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error extracting product details from {product_url}: {str(e)}")
            return None
    
    def download_image(self, image_url, category, product_name, img_index):
        """Download product image"""
        try:
            # Create safe directory and filename
            category_safe = re.sub(r'[^\w\s-]', '', category).strip()
            category_dir = self.images_dir / category_safe.replace(' ', '_').lower()
            category_dir.mkdir(exist_ok=True)
            
            name_safe = re.sub(r'[^\w\s-]', '', product_name[:30]).strip()
            name_safe = name_safe.replace(' ', '_')
            
            # Get file extension
            ext = 'jpg'
            if '.' in image_url:
                ext = image_url.split('.')[-1].split('?')[0].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                    ext = 'jpg'
            
            filename = f"{name_safe}_{img_index}.{ext}"
            filepath = category_dir / filename
            
            # Download image
            response = requests.get(image_url, stream=True, timeout=20)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"📷 Downloaded: {filename}")
                return str(filepath)
                
        except Exception as e:
            logger.warning(f"⚠️  Error downloading image {image_url}: {str(e)}")
            
        return None
    
    def scrape_category(self, category_url):
        """Scrape products from a category"""
        category = category_url.split('/')[-1].replace('.html', '').replace('-', ' ').title()
        logger.info(f"\n🏷️  SCRAPING: {category}")
        logger.info(f"📄 URL: {category_url}")
        
        # Get product links
        product_links = self.get_product_links(category_url)
        if not product_links:
            logger.warning(f"⚠️  No products found in {category}")
            return []
        
        category_products = []
        
        # Process each product
        for i, product_url in enumerate(product_links):
            logger.info(f"\n📦 Product {i+1}/{len(product_links)}")
            
            product = self.extract_product_details(product_url, category)
            if product:
                # Download images (limit to 2 per product for speed)
                for j, img_url in enumerate(product['image_urls'][:2]):
                    self.download_image(img_url, category, product['name'], j)
                    time.sleep(0.5)  # Small delay
                
                category_products.append(product)
                
                # Save progress every 25 products
                if (i + 1) % 25 == 0:
                    self.save_to_csv(category_products, f"{category}_progress_{i+1}")
            
            # Respectful delay between products
            time.sleep(random.uniform(2, 4))
        
        logger.info(f"✅ {category} completed: {len(category_products)} products")
        return category_products
    
    def save_to_csv(self, products, filename):
        """Save products to CSV"""
        if not products:
            return
            
        filepath = self.csv_dir / f"{filename}.csv"
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = products[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in products:
                row = product.copy()
                row['image_urls'] = '; '.join(product['image_urls'])
                writer.writerow(row)
        
        logger.info(f"💾 Saved: {filepath}")
    
    def run(self):
        """Main execution"""
        logger.info("🚀 STARTING PC JEWELLER SCRAPER")
        logger.info("=" * 50)
        
        # Load categories
        try:
            with open('priority_categories.json', 'r') as f:
                categories = json.load(f)
        except FileNotFoundError:
            logger.error("❌ priority_categories.json not found")
            return
        
        # Process categories (limit for testing)
        test_categories = ['rings', 'necklaces', 'earrings']  # Start with these
        
        all_products = []
        
        for category_name in test_categories:
            if category_name in categories:
                logger.info(f"\n🔄 PROCESSING CATEGORY: {category_name.upper()}")
                
                # Process first URL in each category
                category_url = categories[category_name][0]
                products = self.scrape_category(category_url)
                all_products.extend(products)
                
                # Delay between categories
                time.sleep(random.uniform(10, 15))
        
        # Final save
        if all_products:
            self.save_to_csv(all_products, "final_products")
            
            logger.info(f"\n🎉 SCRAPING COMPLETED!")
            logger.info(f"📊 Total products scraped: {len(all_products)}")
            
            # Show sample results
            logger.info(f"\n📋 SAMPLE RESULTS:")
            for i, product in enumerate(all_products[:3]):
                logger.info(f"{i+1}. {product['name']} - {product['price']}")
                logger.info(f"   Category: {product['category']}")
                logger.info(f"   Images: {len(product['image_urls'])}")
        else:
            logger.warning("⚠️  No products were successfully scraped")

def main():
    print("🎯 PC JEWELLER OPTIMIZED SCRAPER")
    print("=" * 40)
    print("✅ Uses correct selectors found by page analysis")
    print("🚀 Ready to extract product data!")
    print()
    
    choice = input("Start scraping with optimized selectors? (y/n): ").lower().strip()
    
    if choice == 'y':
        scraper = PCJewellerScraper(max_products_per_category=150)
        scraper.run()
    else:
        print("👋 Scraping cancelled")

if __name__ == "__main__":
    main()

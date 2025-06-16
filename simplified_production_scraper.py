#!/usr/bin/env python3

import cloudscraper
import time
import json
import csv
import os
import requests
import random
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pathlib import Path
import re

class SimplifiedProductionScraper:
    """Simplified but robust production scraper"""
    
    def __init__(self, max_products_per_category=150):
        self.max_products = max_products_per_category
        self.scraper = cloudscraper.create_scraper()
        self.products = []
        self.images_downloaded = 0
        self.setup_directories()
        
    def setup_directories(self):
        """Create output directories"""
        self.base_dir = Path("scraped_data")
        self.images_dir = self.base_dir / "images"
        self.csv_dir = self.base_dir / "csv"
        
        for directory in [self.base_dir, self.images_dir, self.csv_dir]:
            directory.mkdir(exist_ok=True)
    
    def get_product_links(self, category_url):
        """Extract product links from category page"""
        try:
            print(f"🔍 Getting products from: {category_url}")
            response = self.scraper.get(category_url, timeout=30)
            if response.status_code != 200:
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            product_links = set()
            
            # Find product links
            selectors = [
                'a[href*=".html"]',
                '.productListing a',
                '.pdt-item-list a'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href and href.endswith('.html'):
                        if href.startswith('/'):
                            href = urljoin("https://www.pcjeweller.com", href)
                        
                        # Filter for product pages
                        if any(keyword in href.lower() for keyword in 
                               ['-ring-', '-necklace-', '-earring-', '-bracelet-', '-pendant-']):
                            product_links.add(href)
            
            result = list(product_links)[:self.max_products]
            print(f"✅ Found {len(result)} product links")
            return result
            
        except Exception as e:
            print(f"❌ Error getting links from {category_url}: {e}")
            return []
    
    def extract_product_details(self, product_url, category):
        """Extract product details"""
        try:
            response = self.scraper.get(product_url, timeout=30)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            product = {
                'name': '',
                'price': '',
                'category': category,
                'product_url': product_url,
                'image_urls': []
            }
            
            # Extract name
            name_elem = soup.select_one('h1')
            if name_elem:
                product['name'] = name_elem.get_text(strip=True)
            
            # Extract price from page text (simplified approach)
            page_text = soup.get_text()
            price_match = re.search(r'₹[\\d,]+', page_text)
            if price_match:
                product['price'] = price_match.group()
            
            # Extract images
            images = soup.select('img[src*="catalog/product"]')
            for img in images[:3]:  # Max 3 images
                src = img.get('src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin("https://www.pcjeweller.com", src)
                    product['image_urls'].append(src)
            
            if product['name']:
                print(f"✅ Extracted: {product['name'][:50]}...")
                return product
            
            return None
            
        except Exception as e:
            print(f"❌ Error extracting {product_url}: {e}")
            return None
    
    def download_image(self, image_url, category, product_name, img_index):
        """Download product image"""
        try:
            # Create category directory
            category_dir = self.images_dir / category.lower().replace(' ', '_')
            category_dir.mkdir(exist_ok=True)
            
            # Create safe filename
            name_safe = re.sub(r'[^\\w\\s-]', '', product_name[:30]).strip().replace(' ', '_')
            filename = f"{name_safe}_{img_index}.jpg"
            filepath = category_dir / filename
            
            if filepath.exists():
                return str(filepath)
            
            # Download
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; PCJScraper/1.0)'}
            response = requests.get(image_url, stream=True, timeout=20, headers=headers)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.images_downloaded += 1
                if self.images_downloaded % 10 == 0:
                    print(f"📷 Downloaded {self.images_downloaded} images")
                
                return str(filepath)
                
        except Exception as e:
            print(f"⚠️ Error downloading image: {e}")
            
        return None
    
    def scrape_category(self, category_name, category_urls):
        """Scrape a complete category"""
        print(f"\\n🏷️ SCRAPING: {category_name.upper()}")
        
        all_products = []
        
        for i, url in enumerate(category_urls):
            print(f"\\n📄 URL {i+1}/{len(category_urls)}")
            
            # Get product links
            product_links = self.get_product_links(url)
            if not product_links:
                continue
            
            # Process each product
            for j, product_url in enumerate(product_links):
                if len(all_products) >= self.max_products:
                    break
                    
                print(f"🔄 Product {j+1}/{len(product_links)}: ", end='')
                
                product = self.extract_product_details(product_url, category_name)
                if product:
                    # Download images
                    for k, img_url in enumerate(product['image_urls']):
                        self.download_image(img_url, category_name, product['name'], k)
                        time.sleep(0.5)
                    
                    all_products.append(product)
                
                time.sleep(2)  # Respectful delay
            
            if len(all_products) >= self.max_products:
                break
            
            time.sleep(5)  # Delay between URLs
        
        print(f"✅ {category_name}: {len(all_products)} products completed")
        return all_products
    
    def save_results(self, all_products):
        """Save final results"""
        if not all_products:
            print("⚠️ No products to save")
            return
        
        # Save CSV
        csv_file = self.csv_dir / "all_products_final.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['name', 'price', 'category', 'product_url', 'image_urls']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in all_products:
                row = product.copy()
                row['image_urls'] = '; '.join(product['image_urls'])
                writer.writerow(row)
        
        print(f"💾 Saved {len(all_products)} products to {csv_file}")
        
        # Print summary
        by_category = {}
        for product in all_products:
            cat = product['category']
            by_category[cat] = by_category.get(cat, 0) + 1
        
        print("\\n📊 SUMMARY:")
        for cat, count in by_category.items():
            print(f"  {cat}: {count} products")
        print(f"  📷 Images downloaded: {self.images_downloaded}")
    
    def run_full_scraping(self):
        """Run full production scraping"""
        print("🚀 STARTING SIMPLIFIED PRODUCTION SCRAPER")
        print("=" * 50)
        
        # Load categories
        with open('priority_categories.json', 'r') as f:
            categories = json.load(f)
        
        print(f"📋 Loaded {len(categories)} categories")
        print(f"🎯 Target: {self.max_products} products per category")
        
        all_products = []
        
        # Process each category
        for i, (category_name, category_urls) in enumerate(categories.items()):
            print(f"\\n{'='*50}")
            print(f"🔄 CATEGORY {i+1}/{len(categories)}: {category_name}")
            
            category_products = self.scrape_category(category_name, category_urls)
            all_products.extend(category_products)
            
            # Save progress after each category
            if category_products:
                progress_file = self.csv_dir / f"{category_name}_products.csv"
                with open(progress_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['name', 'price', 'category', 'product_url', 'image_urls']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for product in category_products:
                        row = product.copy()
                        row['image_urls'] = '; '.join(product['image_urls'])
                        writer.writerow(row)
                
                print(f"💾 Progress saved: {progress_file}")
            
            # Long delay between categories
            if i < len(categories) - 1:
                delay = random.uniform(30, 60)
                print(f"⏳ Waiting {delay:.1f}s before next category...")
                time.sleep(delay)
        
        # Save final results
        self.save_results(all_products)
        
        print(f"\\n🎉 SCRAPING COMPLETED!")
        print(f"📊 Total products: {len(all_products)}")
        print(f"📷 Images downloaded: {self.images_downloaded}")
        
        return all_products

def main():
    print("🏭 PC JEWELLER SIMPLIFIED PRODUCTION SCRAPER")
    print("=" * 50)
    
    scraper = SimplifiedProductionScraper(max_products_per_category=150)
    scraper.run_full_scraping()

if __name__ == "__main__":
    main()

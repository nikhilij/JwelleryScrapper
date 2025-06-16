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

def run_final_scraping():
    """Run the final production scraping"""
    
    print("🚀 FINAL PRODUCTION SCRAPING")
    print("=" * 50)
    
    # Setup
    base_dir = Path("scraped_data")
    images_dir = base_dir / "images"
    csv_dir = base_dir / "csv"
    
    for directory in [base_dir, images_dir, csv_dir]:
        directory.mkdir(exist_ok=True)
    
    scraper = cloudscraper.create_scraper()
    
    # Load categories
    with open('priority_categories.json', 'r') as f:
        categories = json.load(f)
    
    print(f"📋 Processing {len(categories)} categories")
    
    all_products = []
    images_downloaded = 0
    
    # Process each category
    for i, (category_name, category_urls) in enumerate(categories.items()):
        print(f"\\n{'='*60}")
        print(f"🔄 CATEGORY {i+1}/{len(categories)}: {category_name.upper()}")
        print(f"📄 URLs to process: {len(category_urls)}")
        
        category_products = []
        
        # Process first 2 URLs per category for efficiency
        for j, url in enumerate(category_urls[:2]):
            print(f"\\n📄 URL {j+1}: {url}")
            
            try:
                # Get category page
                response = scraper.get(url, timeout=30)
                if response.status_code != 200:
                    print(f"❌ Failed to access {url}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find product links
                product_links = set()
                for link in soup.select('a[href*=".html"]'):
                    href = link.get('href')
                    if href and href.endswith('.html'):
                        if href.startswith('/'):
                            href = urljoin("https://www.pcjeweller.com", href)
                        
                        # Filter for product pages
                        if any(keyword in href.lower() for keyword in 
                               ['-ring-', '-necklace-', '-earring-', '-bracelet-', '-pendant-', '-chain-']):
                            product_links.add(href)
                
                product_links = list(product_links)[:50]  # Limit to 50 products per URL
                print(f"✅ Found {len(product_links)} product links")
                
                # Process products
                for k, product_url in enumerate(product_links):
                    if len(category_products) >= 100:  # Max 100 per category
                        break
                    
                    print(f"🔄 Product {k+1}/{len(product_links)}: ", end='', flush=True)
                    
                    try:
                        # Get product page
                        prod_response = scraper.get(product_url, timeout=30)
                        if prod_response.status_code != 200:
                            print("❌ Failed")
                            continue
                        
                        prod_soup = BeautifulSoup(prod_response.content, 'html.parser')
                        
                        # Extract basic info
                        product = {
                            'name': '',
                            'price': '',
                            'category': category_name,
                            'product_url': product_url,
                            'image_urls': []
                        }
                        
                        # Get name
                        name_elem = prod_soup.select_one('h1')
                        if name_elem:
                            product['name'] = name_elem.get_text(strip=True)
                        
                        # Get price (simple extraction)
                        page_text = prod_soup.get_text()
                        price_match = re.search(r'₹[\\d,]+', page_text)
                        if price_match:
                            product['price'] = price_match.group()
                        
                        # Get images
                        for img in prod_soup.select('img[src*="catalog/product"]')[:3]:
                            src = img.get('src')
                            if src:
                                if src.startswith('//'):
                                    src = 'https:' + src
                                elif src.startswith('/'):
                                    src = urljoin("https://www.pcjeweller.com", src)
                                product['image_urls'].append(src)
                        
                        if product['name']:
                            print(f"✅ {product['name'][:30]}...")
                            category_products.append(product)
                            
                            # Download images
                            category_img_dir = images_dir / category_name.lower().replace(' ', '_')
                            category_img_dir.mkdir(exist_ok=True)
                            
                            for img_idx, img_url in enumerate(product['image_urls']):
                                try:
                                    name_safe = re.sub(r'[^\\w\\s-]', '', product['name'][:30]).strip().replace(' ', '_')
                                    img_filename = f"{name_safe}_{img_idx}.jpg"
                                    img_path = category_img_dir / img_filename
                                    
                                    if not img_path.exists():
                                        headers = {'User-Agent': 'Mozilla/5.0 (compatible; Scraper/1.0)'}
                                        img_response = requests.get(img_url, stream=True, timeout=20, headers=headers)
                                        
                                        if img_response.status_code == 200:
                                            with open(img_path, 'wb') as f:
                                                for chunk in img_response.iter_content(chunk_size=8192):
                                                    f.write(chunk)
                                            images_downloaded += 1
                                    
                                    time.sleep(0.2)  # Small delay between images
                                except Exception as e:
                                    pass  # Continue if image download fails
                        else:
                            print("❌ No name found")
                        
                        time.sleep(random.uniform(1, 3))  # Delay between products
                        
                    except Exception as e:
                        print(f"❌ Error: {str(e)[:50]}...")
                        continue
                
                if len(category_products) >= 100:
                    break
                
                time.sleep(5)  # Delay between URLs
                
            except Exception as e:
                print(f"❌ Error processing {url}: {str(e)[:50]}...")
                continue
        
        all_products.extend(category_products)
        
        # Save category progress
        if category_products:
            cat_csv = csv_dir / f"{category_name}_products.csv"
            with open(cat_csv, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['name', 'price', 'category', 'product_url', 'image_urls']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for product in category_products:
                    row = product.copy()
                    row['image_urls'] = '; '.join(product['image_urls'])
                    writer.writerow(row)
            
            print(f"💾 Saved {len(category_products)} products to {cat_csv}")
        
        print(f"✅ {category_name}: {len(category_products)} products completed")
        
        # Delay between categories
        if i < len(categories) - 1:
            delay = random.uniform(15, 30)
            print(f"⏳ Waiting {delay:.1f}s before next category...")
            time.sleep(delay)
    
    # Save final results
    if all_products:
        final_csv = csv_dir / "complete_products_final.csv"
        with open(final_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['name', 'price', 'category', 'product_url', 'image_urls']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in all_products:
                row = product.copy()
                row['image_urls'] = '; '.join(product['image_urls'])
                writer.writerow(row)
        
        print(f"\\n🎉 SCRAPING COMPLETED SUCCESSFULLY!")
        print(f"📊 Total products: {len(all_products)}")
        print(f"📷 Images downloaded: {images_downloaded}")
        print(f"💾 Final results: {final_csv}")
        
        # Category summary
        by_category = {}
        for product in all_products:
            cat = product['category']
            by_category[cat] = by_category.get(cat, 0) + 1
        
        print(f"\\n📋 PRODUCTS BY CATEGORY:")
        for cat, count in sorted(by_category.items()):
            print(f"   {cat}: {count} products")
    
    else:
        print("⚠️ No products were scraped!")

if __name__ == "__main__":
    run_final_scraping()

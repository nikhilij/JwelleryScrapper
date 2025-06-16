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
import re

class AllJewelleryScraper:
    """Comprehensive scraper for all-jewellery and ready-to-ship pages"""
    
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'linux', 'desktop': True}
        )
        self.base_url = "https://www.pcjeweller.com"
        self.setup_directories()
        
    def setup_directories(self):
        """Create output directories"""
        self.base_dir = Path("all_jewellery_data")
        self.images_dir = self.base_dir / "images"
        self.csv_dir = self.base_dir / "csv"
        self.json_dir = self.base_dir / "json"
        
        for directory in [self.base_dir, self.images_dir, self.csv_dir, self.json_dir]:
            directory.mkdir(exist_ok=True)
    
    def extract_all_links_from_page(self, url, page_name):
        """Extract all product links from a page"""
        print(f"🔍 Extracting links from: {page_name}")
        print(f"   URL: {url}")
        
        try:
            response = self.scraper.get(url, timeout=30)
            if response.status_code != 200:
                print(f"❌ Failed to access {url} - Status: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            all_links = set()
            
            # Multiple selectors to catch all possible product links
            selectors = [
                'a[href*=".html"]',                    # All HTML links
                'a[href*="/jewellery/"]',              # Jewellery category links
                'a[href*="ring"]', 'a[href*="earring"]',  # Specific jewelry types
                'a[href*="necklace"]', 'a[href*="pendant"]',
                'a[href*="bracelet"]', 'a[href*="chain"]',
                'a[href*="bangles"]', 'a[href*="mangalsutra"]',
                '.product-item a', '.pdt-item a',      # Product containers
                '.category-link', '.sub-category a',   # Category links
                'a[title*="View"]', 'a[title*="Shop"]' # Action links
            ]
            
            for selector in selectors:
                try:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href')
                        if href:
                            # Clean and normalize URL
                            if href.startswith('/'):
                                href = urljoin(self.base_url, href)
                            elif not href.startswith('http'):
                                href = urljoin(self.base_url, '/' + href)
                            
                            # Remove query parameters and fragments
                            clean_href = href.split('?')[0].split('#')[0]
                            
                            # Filter for relevant links
                            if (clean_href.endswith('.html') and 
                                self.base_url in clean_href and 
                                not any(skip in clean_href.lower() for skip in 
                                       ['login', 'register', 'cart', 'checkout', 'account', 'contact'])):
                                all_links.add(clean_href)
                except Exception as e:
                    print(f"⚠️ Error with selector {selector}: {e}")
                    continue
            
            # Also look for pagination and load more links
            try:
                # Check for pagination
                pagination_links = soup.select('a[href*="page="], a[href*="p="], .pagination a, .load-more')
                for link in pagination_links:
                    href = link.get('href')
                    if href:
                        if href.startswith('/'):
                            href = urljoin(self.base_url, href)
                        
                        # Get additional pages (limit to 10 pages)
                        for page_num in range(2, 11):
                            if 'page=' in href:
                                page_url = re.sub(r'page=\d+', f'page={page_num}', href)
                            else:
                                page_url = f"{href}{'&' if '?' in href else '?'}page={page_num}"
                            
                            print(f"   📄 Checking page {page_num}: {page_url}")
                            try:
                                page_response = self.scraper.get(page_url, timeout=20)
                                if page_response.status_code == 200:
                                    page_soup = BeautifulSoup(page_response.content, 'html.parser')
                                    page_links = page_soup.select('a[href*=".html"]')
                                    
                                    page_count = 0
                                    for page_link in page_links:
                                        page_href = page_link.get('href')
                                        if page_href:
                                            if page_href.startswith('/'):
                                                page_href = urljoin(self.base_url, page_href)
                                            
                                            clean_href = page_href.split('?')[0].split('#')[0]
                                            if (clean_href.endswith('.html') and 
                                                self.base_url in clean_href):
                                                all_links.add(clean_href)
                                                page_count += 1
                                    
                                    print(f"     ✅ Found {page_count} additional links")
                                    if page_count == 0:
                                        break  # No more products on this page
                                else:
                                    break  # Page doesn't exist
                                
                                time.sleep(2)  # Delay between pages
                            except:
                                break  # Stop if page fails
                            
            except Exception as e:
                print(f"⚠️ Error processing pagination: {e}")
            
            result = list(all_links)
            print(f"✅ Total unique links found: {len(result)}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error extracting links from {url}: {str(e)}")
            return []
    
    def extract_product_details(self, product_url):
        """Extract detailed product information"""
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
                'description': '',
                'sku': '',
                'availability': '',
                'product_url': product_url,
                'image_urls': []
            }
            
            # Extract name
            name_selectors = [
                'h1', '.product-name', '.pdt-name', 
                '.product-title', '.item-name', 'title'
            ]
            for selector in name_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    product['name'] = elem.get_text(strip=True)
                    break
            
            # Extract price information
            price_patterns = [
                r'₹\s*[\d,]+',
                r'Rs\.?\s*[\d,]+',
                r'INR\s*[\d,]+',
                r'\$\s*[\d,]+',
                r'Price:?\s*₹?\s*[\d,]+'
            ]
            
            page_text = soup.get_text()
            for pattern in price_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    product['price'] = matches[0].strip()
                    if len(matches) > 1:
                        product['original_price'] = matches[1].strip()
                    break
            
            # Extract images
            img_selectors = [
                'img[src*="catalog/product"]',
                'img[src*="uploads"]',
                'img[src*="pcjeweller"]',
                '.product-image img',
                '.gallery img',
                '.zoom img',
                'img[alt*="Ring"]', 'img[alt*="Earring"]',
                'img[alt*="Necklace"]', 'img[alt*="Pendant"]',
                'img[alt*="Bracelet"]', 'img[alt*="Chain"]'
            ]
            
            for selector in img_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src') or img.get('data-original')
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = urljoin(self.base_url, src)
                        
                        if src not in product['image_urls'] and any(keyword in src.lower() for keyword in 
                                                                   ['catalog', 'upload', 'product', 'jewelry', 'jewellery']):
                            product['image_urls'].append(src)
            
            # Extract additional details from meta tags
            meta_tags = soup.select('meta')
            for meta in meta_tags:
                name = meta.get('name', '').lower()
                content = meta.get('content', '')
                
                if name in ['description', 'og:description'] and not product['description']:
                    product['description'] = content[:400]
                elif name == 'keywords':
                    # Try to extract material info from keywords
                    keywords = content.lower()
                    if 'gold' in keywords:
                        product['metal'] = 'Gold'
                    elif 'silver' in keywords:
                        product['metal'] = 'Silver'
                    elif 'diamond' in keywords:
                        product['stone'] = 'Diamond'
            
            # Extract specifications from structured data
            scripts = soup.select('script[type="application/ld+json"]')
            for script in scripts:
                try:
                    data = json.loads(script.get_text())
                    if isinstance(data, dict):
                        if 'name' in data and not product['name']:
                            product['name'] = data['name']
                        if 'price' in data and not product['price']:
                            product['price'] = str(data['price'])
                        if 'image' in data:
                            images = data['image'] if isinstance(data['image'], list) else [data['image']]
                            for img_url in images:
                                if img_url not in product['image_urls']:
                                    product['image_urls'].append(img_url)
                except:
                    continue
            
            # Try to extract from URL
            if not product['name']:
                url_parts = product_url.split('/')[-1].replace('.html', '').replace('-', ' ')
                product['name'] = url_parts.title()
            
            return product if product['name'] else None
            
        except Exception as e:
            print(f"❌ Error extracting product details from {product_url}: {str(e)}")
            return None
    
    def download_image(self, image_url, product_name, img_index):
        """Download product image"""
        try:
            # Create safe filename
            name_safe = re.sub(r'[^\w\s-]', '', product_name[:40]).strip().replace(' ', '_')
            
            # Get file extension
            ext = 'jpg'
            if '.' in image_url:
                ext = image_url.split('.')[-1].split('?')[0].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                    ext = 'jpg'
            
            filename = f"{name_safe}_{img_index}.{ext}"
            filepath = self.images_dir / filename
            
            # Skip if exists
            if filepath.exists():
                return str(filepath)
            
            # Download
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Referer': 'https://www.pcjeweller.com/'
            }
            
            response = requests.get(image_url, stream=True, timeout=20, headers=headers)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return str(filepath)
            
        except Exception as e:
            print(f"⚠️ Error downloading image {image_url}: {str(e)}")
        
        return None
    
    def run_comprehensive_scraping(self):
        """Main execution function"""
        print("🚀 COMPREHENSIVE PC JEWELLER SCRAPER")
        print("=" * 60)
        print("🎯 Target URLs:")
        print("   • https://www.pcjeweller.com/all-jewellery.html")
        print("   • https://www.pcjeweller.com/ready-to-ship.html")
        print()
        
        # URLs to scrape
        target_urls = {
            'all_jewellery': 'https://www.pcjeweller.com/all-jewellery.html',
            'ready_to_ship': 'https://www.pcjeweller.com/ready-to-ship.html'
        }
        
        all_links = {}
        all_products = []
        images_downloaded = 0
        
        # Phase 1: Extract all links
        print("🔍 PHASE 1: EXTRACTING ALL LINKS")
        print("=" * 40)
        
        for page_name, url in target_urls.items():
            links = self.extract_all_links_from_page(url, page_name)
            all_links[page_name] = links
            
            # Save links to JSON
            links_file = self.json_dir / f"{page_name}_links.json"
            with open(links_file, 'w', encoding='utf-8') as f:
                json.dump(links, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved {len(links)} links to {links_file}")
            time.sleep(5)
        
        # Combine all unique links
        unique_links = set()
        for page_links in all_links.values():
            unique_links.update(page_links)
        
        unique_links = list(unique_links)
        print(f"\\n✅ Total unique links across all pages: {len(unique_links)}")
        
        # Save combined links
        combined_file = self.json_dir / "all_combined_links.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_count': len(unique_links),
                'pages': all_links,
                'all_unique_links': unique_links
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Combined links saved to {combined_file}")
        
        # Phase 2: Extract product details and images
        print(f"\\n🔍 PHASE 2: EXTRACTING PRODUCT DETAILS AND IMAGES")
        print("=" * 50)
        print(f"📦 Processing {len(unique_links)} unique product links...")
        
        for i, product_url in enumerate(unique_links):
            print(f"\\n🔄 Product {i+1}/{len(unique_links)}: ", end='', flush=True)
            
            # Extract product details
            product = self.extract_product_details(product_url)
            if product:
                print(f"✅ {product['name'][:50]}...")
                
                # Download images
                for j, img_url in enumerate(product['image_urls'][:5]):  # Max 5 images per product
                    downloaded_path = self.download_image(img_url, product['name'], j)
                    if downloaded_path:
                        images_downloaded += 1
                    time.sleep(0.3)  # Small delay between images
                
                all_products.append(product)
                
                # Save progress every 50 products
                if len(all_products) % 50 == 0:
                    self.save_progress(all_products, f"progress_{len(all_products)}")
                    print(f"\\n💾 Progress saved: {len(all_products)} products, {images_downloaded} images")
            else:
                print("❌ Failed to extract")
            
            # Respectful delay
            time.sleep(random.uniform(2, 4))
            
            # Optional: Limit for testing (remove for full scraping)
            # if len(all_products) >= 100:
            #     print(f"\\n⚠️ Stopped at {len(all_products)} products for testing")
            #     break
        
        # Phase 3: Save final results
        print(f"\\n💾 PHASE 3: SAVING FINAL RESULTS")
        print("=" * 40)
        
        self.save_final_results(all_products, images_downloaded)
        
        print(f"\\n🎉 SCRAPING COMPLETED SUCCESSFULLY!")
        print(f"📊 Final Statistics:")
        print(f"   🔗 Total unique links: {len(unique_links)}")
        print(f"   📦 Products extracted: {len(all_products)}")
        print(f"   📷 Images downloaded: {images_downloaded}")
        print(f"   📁 Results saved in: {self.base_dir}")
        
        return all_products
    
    def save_progress(self, products, filename):
        """Save progress to files"""
        if not products:
            return
        
        # Save CSV
        progress_csv = self.csv_dir / f"{filename}.csv"
        with open(progress_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = products[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in products:
                row = product.copy()
                row['image_urls'] = '; '.join(product['image_urls'])
                writer.writerow(row)
        
        # Save JSON
        progress_json = self.json_dir / f"{filename}.json"
        with open(progress_json, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
    
    def save_final_results(self, products, images_count):
        """Save final comprehensive results"""
        if not products:
            print("⚠️ No products to save")
            return
        
        # Save master CSV
        final_csv = self.csv_dir / "all_jewellery_complete.csv"
        with open(final_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = products[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in products:
                row = product.copy()
                row['image_urls'] = '; '.join(product['image_urls'])
                writer.writerow(row)
        
        # Save master JSON
        final_json = self.json_dir / "all_jewellery_complete.json"
        with open(final_json, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        # Save statistics
        stats = {
            'scraping_completed': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_products': len(products),
            'images_downloaded': images_count,
            'source_urls': [
                'https://www.pcjeweller.com/all-jewellery.html',
                'https://www.pcjeweller.com/ready-to-ship.html'
            ]
        }
        
        stats_file = self.json_dir / "scraping_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Final results saved:")
        print(f"   📊 {final_csv}")
        print(f"   📊 {final_json}")
        print(f"   📊 {stats_file}")

def main():
    print("🏭 PC JEWELLER ALL-JEWELLERY COMPREHENSIVE SCRAPER")
    print("=" * 60)
    print("🎯 This will scrape:")
    print("   • All product links from all-jewellery.html")
    print("   • All product links from ready-to-ship.html")
    print("   • Product details for each link")
    print("   • All product images")
    print()
    
    choice = input("Start comprehensive scraping? (y/n): ").lower().strip()
    
    if choice == 'y':
        scraper = AllJewelleryScraper()
        scraper.run_comprehensive_scraping()
    else:
        print("👋 Scraping cancelled")

if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import random

class PCJewellerScraper:
    def __init__(self):
        self.base_url = "https://www.pcjeweller.com"
        self.target_url = "https://www.pcjeweller.com/all-jewellery.html"
        self.session = requests.Session()
        
        # More comprehensive headers to mimic a real browser
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Linux"'
        })
    
    def extract_all_links(self):
        """Extract all links from the PC Jeweller all-jewellery page"""
        try:
            print(f"Fetching page: {self.target_url}")
            
            # Add a small delay to be respectful
            time.sleep(random.uniform(1, 3))
            
            # Try to get the page first without following redirects
            response = self.session.get(self.target_url, timeout=30, allow_redirects=True)
            
            print(f"Response status code: {response.status_code}")
            print(f"Final URL: {response.url}")
            
            if response.status_code == 403:
                print("Access forbidden. Trying alternative approach...")
                # Try with minimal headers
                simple_headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                }
                response = requests.get(self.target_url, headers=simple_headers, timeout=30)
                print(f"Alternative approach status code: {response.status_code}")
            
            response.raise_for_status()
            
            print(f"Successfully fetched page. Content length: {len(response.content)} bytes")
            
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all anchor tags with href attributes
            links = soup.find_all('a', href=True)
            
            extracted_links = []
            unique_links = set()
            
            for link in links:
                href = link['href'].strip()
                
                # Skip empty links, javascript links, and mail links
                if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                    continue
                
                # Convert relative URLs to absolute URLs
                if href.startswith('/'):
                    full_url = urljoin(self.base_url, href)
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(self.target_url, href)
                
                # Add to unique set and list
                if full_url not in unique_links:
                    unique_links.add(full_url)
                    
                    # Get link text
                    link_text = link.get_text(strip=True)
                    
                    extracted_links.append({
                        'url': full_url,
                        'text': link_text,
                        'title': link.get('title', ''),
                        'class': link.get('class', [])
                    })
            
            return extracted_links
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the page: {e}")
            return []
        except Exception as e:
            print(f"Error parsing the page: {e}")
            return []
    
    def save_links_to_file(self, links, filename='extracted_links.json'):
        """Save extracted links to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(links, f, indent=2, ensure_ascii=False)
            print(f"Links saved to {filename}")
        except Exception as e:
            print(f"Error saving links to file: {e}")
    
    def save_links_to_text(self, links, filename='extracted_links.txt'):
        """Save extracted links to a text file (URLs only)"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for link in links:
                    f.write(f"{link['url']}\n")
            print(f"Links saved to {filename}")
        except Exception as e:
            print(f"Error saving links to text file: {e}")
    
    def filter_product_links(self, links):
        """Filter links that are likely product pages"""
        product_links = []
        product_keywords = ['product', 'jewellery', 'jewelry', 'ring', 'necklace', 'earring', 'bracelet', 'pendant']
        
        for link in links:
            url_lower = link['url'].lower()
            text_lower = link['text'].lower()
            
            # Check if URL or text contains product-related keywords
            if any(keyword in url_lower or keyword in text_lower for keyword in product_keywords):
                product_links.append(link)
        
        return product_links

def main():
    scraper = PCJewellerScraper()
    
    print("Starting PC Jeweller link extraction...")
    print("="*50)
    
    # Extract all links
    all_links = scraper.extract_all_links()
    
    if all_links:
        print(f"\nTotal links found: {len(all_links)}")
        
        # Save all links to files
        scraper.save_links_to_file(all_links, 'all_links.json')
        scraper.save_links_to_text(all_links, 'all_links.txt')
        
        # Filter and save product links
        product_links = scraper.filter_product_links(all_links)
        print(f"Product-related links found: {len(product_links)}")
        
        if product_links:
            scraper.save_links_to_file(product_links, 'product_links.json')
            scraper.save_links_to_text(product_links, 'product_links.txt')
        
        # Display first 10 links as sample
        print("\nSample links (first 10):")
        print("-" * 50)
        for i, link in enumerate(all_links[:10]):
            print(f"{i+1}. {link['url']}")
            if link['text']:
                print(f"   Text: {link['text']}")
            print()
        
        if len(all_links) > 10:
            print(f"... and {len(all_links) - 10} more links")
    else:
        print("No links found or error occurred during scraping.")

if __name__ == "__main__":
    main()

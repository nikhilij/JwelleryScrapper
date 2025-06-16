import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class PCJewellerSeleniumScraper:
    def __init__(self):
        self.base_url = "https://www.pcjeweller.com"
        self.target_url = "https://www.pcjeweller.com/all-jewellery.html"
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver with options to avoid detection"""
        chrome_options = Options()
        
        # Add arguments to make the browser look more like a real user
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        
        # For headless operation
        chrome_options.add_argument("--headless")
        
        try:
            # Try to use system chromium first
            chrome_options.binary_location = "/usr/bin/chromium-browser"
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("Successfully initialized Chrome WebDriver")
            return True
        except Exception as e:
            print(f"Error with system chromium: {e}")
            try:
                # Fallback to ChromeDriverManager
                self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                print("Successfully initialized Chrome WebDriver with ChromeDriverManager")
                return True
            except Exception as e2:
                print(f"Error setting up Chrome driver: {e2}")
                return False
    
    def extract_all_links(self):
        """Extract all links using Selenium"""
        if not self.setup_driver():
            return []
        
        try:
            print(f"Loading page: {self.target_url}")
            self.driver.get(self.target_url)
            
            # Wait for the page to load
            print("Waiting for page to load...")
            time.sleep(5)
            
            # Wait for any dynamic content to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "a"))
                )
            except TimeoutException:
                print("Timeout waiting for links to load, proceeding anyway...")
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            print(f"Page loaded successfully. Title: {self.driver.title}")
            print(f"Current URL: {self.driver.current_url}")
            
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
            
        except WebDriverException as e:
            print(f"WebDriver error: {e}")
            return []
        except Exception as e:
            print(f"Error extracting links: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
    
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
        product_keywords = ['product', 'jewellery', 'jewelry', 'ring', 'necklace', 'earring', 'bracelet', 'pendant', 'gold', 'diamond', 'silver']
        
        for link in links:
            url_lower = link['url'].lower()
            text_lower = link['text'].lower()
            
            # Check if URL or text contains product-related keywords
            if any(keyword in url_lower or keyword in text_lower for keyword in product_keywords):
                product_links.append(link)
        
        return product_links

def main():
    scraper = PCJewellerSeleniumScraper()
    
    print("Starting PC Jeweller link extraction with Selenium...")
    print("="*60)
    
    # Extract all links
    all_links = scraper.extract_all_links()
    
    if all_links:
        print(f"\nTotal links found: {len(all_links)}")
        
        # Save all links to files
        scraper.save_links_to_file(all_links, 'all_links_selenium.json')
        scraper.save_links_to_text(all_links, 'all_links_selenium.txt')
        
        # Filter and save product links
        product_links = scraper.filter_product_links(all_links)
        print(f"Product-related links found: {len(product_links)}")
        
        if product_links:
            scraper.save_links_to_file(product_links, 'product_links_selenium.json')
            scraper.save_links_to_text(product_links, 'product_links_selenium.txt')
        
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

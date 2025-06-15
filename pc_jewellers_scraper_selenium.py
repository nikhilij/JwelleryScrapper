import asyncio
import logging
import json
import csv
import os
import random
import time
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from config import (
    BASE_URL, OUTPUT_DIR, LOG_DIR, SCRAPING_CONFIG, 
    CATEGORIES, SELECTORS, USER_AGENTS, OUTPUT_CONFIG, LOGGING_CONFIG
)


class PCJewellersScraper:
    """
    Selenium-based scraper for PC Jewellers website.
    Handles JavaScript rendering, dynamic content loading, and anti-bot measures.
    """
    
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
        self.scraped_data = []
        self.driver = None
        self.session_stats = {
            "products_scraped": 0,
            "categories_processed": 0,
            "errors": 0,
            "start_time": datetime.now()
        }
    
    def setup_logging(self):
        """Configure logging for the scraper."""
        os.makedirs(LOG_DIR, exist_ok=True)
        
        log_filename = f"pc_jewellers_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_path = os.path.join(LOG_DIR, log_filename)
        
        logging.basicConfig(
            level=getattr(logging, LOGGING_CONFIG["level"]),
            format=LOGGING_CONFIG["format"],
            handlers=[
                logging.FileHandler(log_path) if LOGGING_CONFIG["file_logging"] else logging.NullHandler(),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("PC Jewellers Scraper initialized")
    
    def setup_directories(self):
        """Create necessary directories."""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
    
    def create_driver(self):
        """Create a stealth Chrome WebDriver with anti-detection measures."""
        chrome_options = Options()
        
        if SCRAPING_CONFIG["headless"]:
            chrome_options.add_argument("--headless")
        
        # Anti-detection arguments
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
        
        # Disable automation indicators
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Create driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def wait_with_random_delay(self, base_delay: float = None):
        """Add random delay to appear more human-like."""
        if base_delay is None:
            base_delay = SCRAPING_CONFIG["delay_between_requests"]
        
        # Add random variation (±20%)
        delay = base_delay + random.uniform(-base_delay * 0.2, base_delay * 0.2)
        time.sleep(delay)
    
    def navigate_to_category(self, category: Dict) -> bool:
        """Navigate to a specific category page."""
        try:
            self.logger.info(f"Navigating to category: {category['name']}")
            
            # Try direct URL first
            category_url = urljoin(BASE_URL, category['url'])
            self.driver.get(category_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, SCRAPING_CONFIG["timeout"] // 1000).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            self.wait_with_random_delay()
            return True
            
        except Exception as e:
            self.logger.error(f"Error navigating to category {category['name']}: {str(e)}")
            return False
    
    def scroll_and_load_content(self) -> None:
        """Scroll page and trigger any lazy loading."""
        try:
            # Get page height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # Scroll down to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for new content to load
                time.sleep(2)
                
                # Check for load more buttons
                try:
                    load_more_selectors = [
                        "button[class*='load-more']",
                        "button[class*='show-more']", 
                        "a[class*='load-more']",
                        ".load-more",
                        ".show-more"
                    ]
                    
                    for selector in load_more_selectors:
                        try:
                            load_more_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if load_more_btn.is_displayed():
                                self.driver.execute_script("arguments[0].click();", load_more_btn)
                                time.sleep(3)
                                break
                        except NoSuchElementException:
                            continue
                except:
                    pass
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
              # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            self.logger.error(f"Error during scrolling: {str(e)}")
    
    def extract_product_data(self, category_name: str) -> List[Dict]:
        """Extract product data from current page using BeautifulSoup."""
        html_content = self.driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        
        # Find product containers using multiple selectors
        product_containers = []
        
        # Try configured selector first
        if SELECTORS["product_container"]:
            product_containers = soup.select(SELECTORS["product_container"])
        
        # Fallback selectors if no products found
        if not product_containers:
            fallback_selectors = [
                ".product", ".item", ".card", "[data-product-id]",
                ".product-list-item", ".grid-item", ".product-tile",
                "[class*='product']", "[class*='item']", "article",
                ".listing-item", ".catalog-item", ".shop-item"
            ]
            
            for selector in fallback_selectors:
                product_containers = soup.select(selector)
                if len(product_containers) >= 5:  # Reasonable number of products
                    self.logger.info(f"Using fallback selector: {selector}")
                    break
        
        self.logger.info(f"Found {len(product_containers)} product containers for {category_name}")
        
        # Extract from each container
        for i, container in enumerate(product_containers):
            try:
                product_data = self.extract_single_product(container, category_name)
                if product_data:
                    products.append(product_data)
                    
                    # Log progress for every 10 products
                    if (i + 1) % 10 == 0:
                        self.logger.info(f"Extracted {len(products)} products so far from {category_name}")
                        
                # Stop if we've reached the maximum for this category
                max_products = SCRAPING_CONFIG["max_products_per_category"]
                if max_products > 0 and len(products) >= max_products:
                    self.logger.info(f"Reached maximum limit of {max_products} products for {category_name}")
                    break
                    
            except Exception as e:
                self.logger.error(f"Error extracting product data: {str(e)}")
                continue
        
        return products
      
    def extract_single_product(self, container, category_name: str) -> Optional[Dict]:
        """Extract data from a single product container."""
        try:
            # Extract product name
            name_element = container.select_one(SELECTORS["product_name"])
            if not name_element:
                # Try alternative selectors
                name_selectors = ["h1", "h2", "h3", "h4", ".title", ".name", "[class*='title']", "[class*='name']", 
                                 "span[class*='name']", "div[class*='title']", "[title]"]
                for selector in name_selectors:
                    name_element = container.select_one(selector)
                    if name_element and name_element.get_text(strip=True):
                        break
            
            product_name = name_element.get_text(strip=True) if name_element else ""
            
            # Extract price
            price_element = container.select_one(SELECTORS["product_price"])
            if not price_element:
                # Try alternative selectors
                price_selectors = [".amount", ".cost", ".value", "[data-price]", "[class*='price']", "[class*='cost']",
                                 "span[class*='price']", "div[class*='price']", ".currency", "[class*='amount']"]
                for selector in price_selectors:
                    price_element = container.select_one(selector)
                    if price_element:
                        price_text = price_element.get_text(strip=True)
                        if any(char in price_text for char in ['₹', '$', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
                            break
            
            product_price = price_element.get_text(strip=True) if price_element else "N/A"
            
            # Extract image URL
            img_element = container.select_one("img")
            image_url = ""
            if img_element:
                image_url = (img_element.get('src') or 
                            img_element.get('data-src') or 
                            img_element.get('data-lazy') or 
                            img_element.get('data-original') or
                            img_element.get('data-srcset'))
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(BASE_URL, image_url)
            
            # Extract product URL
            link_element = container.select_one("a")
            product_url = ""
            if link_element:
                href = link_element.get('href')
                if href:
                    product_url = urljoin(BASE_URL, href) if not href.startswith('http') else href
            
            # Extract metal type
            metal_type = self.extract_metal_type(container, product_name)
            
            # Extract weight
            weight = self.extract_weight(container, product_name)
            
            # Skip if essential data is missing
            if not product_name or len(product_name) < 3:
                return None
            
            return {
                "name": product_name,
                "price": product_price,
                "image_url": image_url,
                "product_url": product_url,
                "metal_type": metal_type,
                "weight": weight,
                "category": category_name,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting single product: {str(e)}")
            return None
    
    def scrape_category(self, category: Dict) -> List[Dict]:
        """Scrape all products from a specific category."""
        self.logger.info(f"Starting to scrape category: {category['name']}")
        
        if not self.navigate_to_category(category):
            return []
        
        # Wait for content to load
        time.sleep(3)
        
        # Scroll and load all content
        self.scroll_and_load_content()
        
        # Extract products
        products = self.extract_product_data(category['name'])
        
        # Limit products if configured
        max_products = SCRAPING_CONFIG["max_products_per_category"]
        if max_products > 0 and len(products) > max_products:
            products = products[:max_products]
        
        self.logger.info(f"Scraped {len(products)} products from {category['name']}")
        self.session_stats["products_scraped"] += len(products)
        self.session_stats["categories_processed"] += 1
        
        return products
    
    def scrape_all_categories(self):
        """Main scraping method to scrape all configured categories."""
        self.logger.info("Starting PC Jewellers scraping session")
        
        self.driver = self.create_driver()
        
        try:
            for category in CATEGORIES:
                try:
                    products = self.scrape_category(category)
                    self.scraped_data.extend(products)
                    
                    # Wait between categories
                    self.wait_with_random_delay(SCRAPING_CONFIG["delay_between_categories"])
                    
                except Exception as e:
                    self.logger.error(f"Error scraping category {category['name']}: {str(e)}")
                    self.session_stats["errors"] += 1
                    continue
        
        finally:
            if self.driver:
                self.driver.quit()
        
        self.session_stats["end_time"] = datetime.now()
        self.logger.info(f"Scraping session completed. Total products: {len(self.scraped_data)}")
    
    def save_data(self):
        """Save scraped data to files."""
        if not self.scraped_data:
            self.logger.warning("No data to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to CSV
        if OUTPUT_CONFIG["save_csv"]:
            csv_filename = f"pc_jewellers_products_{timestamp}.csv" if OUTPUT_CONFIG["include_timestamp"] else "pc_jewellers_products.csv"
            csv_path = os.path.join(OUTPUT_DIR, csv_filename)
            
            # Write CSV manually
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                if self.scraped_data:
                    fieldnames = self.scraped_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.scraped_data)
            self.logger.info(f"Data saved to CSV: {csv_path}")
        
        # Save to JSON
        if OUTPUT_CONFIG["save_json"]:
            json_filename = f"pc_jewellers_products_{timestamp}.json" if OUTPUT_CONFIG["include_timestamp"] else "pc_jewellers_products.json"
            json_path = os.path.join(OUTPUT_DIR, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Data saved to JSON: {json_path}")
        
        # Save session statistics
        stats_path = os.path.join(OUTPUT_DIR, f"session_stats_{timestamp}.json")
        with open(stats_path, 'w') as f:
            stats = self.session_stats.copy()
            stats["start_time"] = stats["start_time"].isoformat()
            stats["end_time"] = stats["end_time"].isoformat()
            stats["duration"] = str(stats["end_time"] - stats["start_time"])
            json.dump(stats, f, indent=2)
    
    def print_summary(self):
        """Print scraping session summary."""
        duration = self.session_stats["end_time"] - self.session_stats["start_time"]
        
        print("\n" + "="*50)
        print("PC JEWELLERS SCRAPING SUMMARY")
        print("="*50)
        print(f"Duration: {duration}")
        print(f"Categories processed: {self.session_stats['categories_processed']}")
        print(f"Products scraped: {self.session_stats['products_scraped']}")
        print(f"Errors encountered: {self.session_stats['errors']}")
        print(f"Success rate: {((self.session_stats['categories_processed'] - self.session_stats['errors']) / len(CATEGORIES) * 100):.1f}%")
        
        if self.scraped_data:
            categories = set(item['category'] for item in self.scraped_data)
            print(f"Categories with data: {', '.join(categories)}")
        
        print("="*50)
    
    def extract_metal_type(self, container, product_name: str) -> str:
        """Extract metal type from product container or name."""
        try:
            # First try to find metal type in dedicated elements
            metal_selectors = [
                "[class*='metal']", "[data-metal]", ".material", "[class*='material']",
                ".specification", "[class*='spec']", ".details", "[class*='detail']"
            ]
            
            for selector in metal_selectors:
                element = container.select_one(selector)
                if element:
                    text = element.get_text(strip=True).lower()
                    metal_type = self.identify_metal_from_text(text)
                    if metal_type != "unknown":
                        return metal_type
            
            # Fallback: extract from product name
            return self.identify_metal_from_text(product_name.lower())
            
        except Exception as e:
            self.logger.debug(f"Error extracting metal type: {str(e)}")
            return "unknown"
    
    def extract_weight(self, container, product_name: str) -> str:
        """Extract weight from product container or name."""
        try:
            # Try to find weight in dedicated elements
            weight_selectors = [
                "[class*='weight']", "[data-weight]", ".weight", ".grams", "[class*='gram']",
                ".specification", "[class*='spec']", ".details", "[class*='detail']"
            ]
            
            for selector in weight_selectors:
                element = container.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    weight = self.extract_weight_from_text(text)
                    if weight != "unknown":
                        return weight
            
            # Fallback: extract from product name and description
            all_text = product_name
            
            # Check if there are any description elements
            desc_selectors = [".description", "[class*='desc']", ".info", "[class*='info']"]
            for selector in desc_selectors:
                desc_element = container.select_one(selector)
                if desc_element:
                    all_text += " " + desc_element.get_text(strip=True)
            
            return self.extract_weight_from_text(all_text)
            
        except Exception as e:
            self.logger.debug(f"Error extracting weight: {str(e)}")
            return "unknown"
    
    def identify_metal_from_text(self, text: str) -> str:
        """Identify metal type from text content."""
        text = text.lower()
        
        # Define metal keywords with priority
        metal_keywords = {
            "gold": ["gold", "au", "yellow gold", "white gold", "rose gold", "14k", "18k", "22k", "24k"],
            "silver": ["silver", "ag", "sterling silver", "925", "silver 925"],
            "platinum": ["platinum", "pt", "plat"],
            "diamond": ["diamond", "diamonds", "solitaire", "brilliant"],
            "pearl": ["pearl", "pearls"],
            "titanium": ["titanium", "ti"],
            "stainless steel": ["stainless", "steel", "ss"],
            "brass": ["brass"],
            "copper": ["copper", "cu"],
            "alloy": ["alloy", "metal alloy"]
        }
        
        for metal_type, keywords in metal_keywords.items():
            if any(keyword in text for keyword in keywords):
                return metal_type
        
        return "unknown"
    
    def extract_weight_from_text(self, text: str) -> str:
        """Extract weight information from text."""
        import re
        
        # Look for weight patterns
        weight_patterns = [
            r'(\d+\.?\d*)\s*(?:gm|gms|gram|grams|g)\b',
            r'(\d+\.?\d*)\s*(?:ct|carat|carats)\b',
            r'(\d+\.?\d*)\s*(?:oz|ounce|ounces)\b',
            r'(\d+\.?\d*)\s*(?:dwt|pennyweight)\b'
        ]
        
        for pattern in weight_patterns:
            match = re.search(pattern, text.lower())
            if match:
                weight_value = match.group(1)
                unit = text[match.start():match.end()].split()[-1]
                return f"{weight_value} {unit}"
        
        return "unknown"


def main():
    """Main function to run the scraper."""
    scraper = PCJewellersScraper()
    
    try:
        scraper.scrape_all_categories()
        scraper.save_data()
        scraper.print_summary()
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        if scraper.scraped_data:
            scraper.save_data()
            print("Partial data saved")
        
    except Exception as e:
        scraper.logger.error(f"Unexpected error: {str(e)}")
        if scraper.scraped_data:
            scraper.save_data()


if __name__ == "__main__":
    main()

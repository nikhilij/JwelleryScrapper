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

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup

from config import (
    BASE_URL, OUTPUT_DIR, LOG_DIR, SCRAPING_CONFIG, 
    CATEGORIES, SELECTORS, USER_AGENTS, OUTPUT_CONFIG, LOGGING_CONFIG
)


class PCJewellersScraper:
    """
    Advanced Playwright-based scraper for PC Jewellers website.
    Handles JavaScript rendering, dynamic content loading, and anti-bot measures.
    """
    
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
        self.scraped_data = []
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
    
    async def create_browser_context(self, playwright):
        """Create a stealth browser context with anti-detection measures."""
        browser = await playwright.chromium.launch(
            headless=SCRAPING_CONFIG["headless"],
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
        )
        
        # Create context with stealth settings
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        
        # Add stealth script to bypass detection
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            window.chrome = {
                runtime: {},
            };
        """)
        
        return browser, context
    
    async def wait_with_random_delay(self, base_delay: float = None):
        """Add random delay to appear more human-like."""
        if base_delay is None:
            base_delay = SCRAPING_CONFIG["delay_between_requests"]
        
        # Add random variation (±20%)
        delay = base_delay + random.uniform(-base_delay * 0.2, base_delay * 0.2)
        await asyncio.sleep(delay)
    
    async def navigate_to_category(self, page: Page, category: Dict) -> bool:
        """Navigate to a specific category page."""
        try:
            self.logger.info(f"Navigating to category: {category['name']}")
            
            # Try direct URL first
            category_url = urljoin(BASE_URL, category['url'])
            
            response = await page.goto(
                category_url, 
                wait_until="networkidle",
                timeout=SCRAPING_CONFIG["timeout"]
            )
            
            if response and response.status == 200:
                await self.wait_with_random_delay()
                return True
            
            # Fallback: try to find and click category link
            self.logger.info(f"Direct navigation failed, trying to find category link")
            await page.goto(BASE_URL, wait_until="networkidle")
            
            # Wait for page to load and try to find category
            await page.wait_for_timeout(2000)
            
            # Try multiple possible selectors for the category
            category_selectors = [
                category['selector'],
                f"a:has-text('{category['name'].title()}')",
                f"a[href*='{category['name']}']",
                f"text={category['name'].title()}"
            ]
            
            for selector in category_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        await element.click()
                        await page.wait_for_load_state("networkidle")
                        await self.wait_with_random_delay()
                        return True
                except:
                    continue
            
            self.logger.warning(f"Could not navigate to category: {category['name']}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error navigating to category {category['name']}: {str(e)}")
            return False
    
    async def scroll_and_load_content(self, page: Page) -> None:
        """Scroll page and trigger any lazy loading."""
        try:
            # Get page height
            page_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = await page.evaluate("window.innerHeight")
            
            # Scroll in chunks
            current_position = 0
            scroll_step = viewport_height // 2
            
            while current_position < page_height:
                await page.evaluate(f"window.scrollTo(0, {current_position})")
                await asyncio.sleep(0.5)  # Wait for lazy loading
                
                # Check for load more buttons
                load_more_buttons = await page.query_selector_all(SELECTORS["load_more_button"])
                for button in load_more_buttons:
                    try:
                        if await button.is_visible():
                            await button.click()
                            await page.wait_for_timeout(2000)
                            break
                    except:
                        pass
                
                current_position += scroll_step
                
                # Update page height in case new content loaded
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height > page_height:
                    page_height = new_height
            
            # Scroll back to top
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
            
        except Exception as e:
            self.logger.error(f"Error during scrolling: {str(e)}")
    
    def extract_product_data(self, html_content: str, category_name: str) -> List[Dict]:
        """Extract product data from HTML using BeautifulSoup."""
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        
        # Find product containers
        product_containers = soup.select(SELECTORS["product_container"])
        
        if not product_containers:
            # Fallback: try common e-commerce selectors
            fallback_selectors = [
                ".product", ".item", ".card", "[data-product-id]",
                ".product-list-item", ".grid-item", ".product-tile"
            ]
            
            for selector in fallback_selectors:
                product_containers = soup.select(selector)
                if product_containers:
                    break
        
        self.logger.info(f"Found {len(product_containers)} product containers for {category_name}")
        
        for container in product_containers:
            try:
                product_data = self.extract_single_product(container, category_name)
                if product_data:
                    products.append(product_data)
                    
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
                name_element = container.select_one("h1, h2, h3, h4, .title, .name")
            
            product_name = name_element.get_text(strip=True) if name_element else "N/A"
            
            # Extract price
            price_element = container.select_one(SELECTORS["product_price"])
            if not price_element:
                # Try alternative selectors
                price_element = container.select_one(".amount, .cost, .value, [data-price]")
            
            product_price = price_element.get_text(strip=True) if price_element else "N/A"
            
            # Extract image URL
            img_element = container.select_one(SELECTORS["product_image"])
            image_url = ""
            if img_element:
                image_url = img_element.get('src') or img_element.get('data-src') or img_element.get('data-lazy')
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(BASE_URL, image_url)
            
            # Extract product URL
            link_element = container.select_one(SELECTORS["product_link"])
            if not link_element:
                link_element = container.find('a')
            
            product_url = ""
            if link_element:
                href = link_element.get('href')
                if href:
                    product_url = urljoin(BASE_URL, href) if not href.startswith('http') else href
            
            # Skip if essential data is missing
            if product_name == "N/A" or not product_name:
                return None
            
            return {
                "name": product_name,
                "price": product_price,
                "image_url": image_url,
                "product_url": product_url,
                "category": category_name,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting single product: {str(e)}")
            return None
    
    async def scrape_category(self, page: Page, category: Dict) -> List[Dict]:
        """Scrape all products from a specific category."""
        self.logger.info(f"Starting to scrape category: {category['name']}")
        
        if not await self.navigate_to_category(page, category):
            return []
        
        # Wait for content to load
        await page.wait_for_timeout(3000)
        
        # Scroll and load all content
        await self.scroll_and_load_content(page)
        
        # Get page content and extract products
        html_content = await page.content()
        products = self.extract_product_data(html_content, category['name'])
        
        # Limit products if configured
        max_products = SCRAPING_CONFIG["max_products_per_category"]
        if max_products > 0 and len(products) > max_products:
            products = products[:max_products]
        
        self.logger.info(f"Scraped {len(products)} products from {category['name']}")
        self.session_stats["products_scraped"] += len(products)
        self.session_stats["categories_processed"] += 1
        
        return products
    
    async def scrape_all_categories(self):
        """Main scraping method to scrape all configured categories."""
        self.logger.info("Starting PC Jewellers scraping session")
        
        async with async_playwright() as playwright:
            browser, context = await self.create_browser_context(playwright)
            
            try:
                page = await context.new_page()
                
                # Set additional page properties
                await page.set_extra_http_headers({
                    "Referer": BASE_URL
                })
                
                for category in CATEGORIES:
                    try:
                        products = await self.scrape_category(page, category)
                        self.scraped_data.extend(products)
                        
                        # Wait between categories
                        await self.wait_with_random_delay(SCRAPING_CONFIG["delay_between_categories"])
                        
                    except Exception as e:
                        self.logger.error(f"Error scraping category {category['name']}: {str(e)}")
                        self.session_stats["errors"] += 1
                        continue
                
            finally:
                await browser.close()
        
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
            
            # Write CSV manually without pandas
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


async def main():
    """Main function to run the scraper."""
    scraper = PCJewellersScraper()
    
    try:
        await scraper.scrape_all_categories()
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
    asyncio.run(main())

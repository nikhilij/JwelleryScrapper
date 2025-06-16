import json
import os
import time
import random
import requests
import cloudscraper
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import logging
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickTester:
    def __init__(self):
        self.ua = UserAgent()
        self.cloudscraper_session = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'linux', 'desktop': True}
        )
        
    def test_category_access(self, url):
        """Test if we can access a category page"""
        try:
            response = self.cloudscraper_session.get(url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('title')
                logger.info(f"✅ SUCCESS: {url}")
                logger.info(f"   📄 Title: {title.text[:100] if title else 'No title'}")
                
                # Look for product links
                product_links = []
                selectors = ['a[href*="product"]', 'a[href*=".html"] img', '.product-item a']
                for selector in selectors:
                    links = soup.select(selector)
                    for link in links[:5]:  # Just first 5
                        href = link.get('href')
                        if href and 'product' in href.lower():
                            if href.startswith('/'):
                                href = urljoin("https://www.pcjeweller.com", href)
                            product_links.append(href)
                
                logger.info(f"   🔗 Found {len(product_links)} potential product links")
                return True, product_links[:3]  # Return first 3 for testing
                
            else:
                logger.error(f"❌ FAILED: {url} - Status: {response.status_code}")
                return False, []
                
        except Exception as e:
            logger.error(f"❌ ERROR: {url} - {str(e)}")
            return False, []
    
    def test_product_page(self, url):
        """Test if we can scrape a product page"""
        try:
            response = self.cloudscraper_session.get(url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract basic info
                title = soup.find('title')
                price_elem = soup.select_one('.price, .amount, [class*="price"]')
                image_elem = soup.select_one('img[src*="product"], .product-image img')
                
                logger.info(f"✅ PRODUCT SUCCESS: {url}")
                logger.info(f"   📄 Title: {title.text[:100] if title else 'No title'}")
                logger.info(f"   💰 Price found: {'Yes' if price_elem else 'No'}")
                logger.info(f"   🖼️  Image found: {'Yes' if image_elem else 'No'}")
                
                return True
            else:
                logger.error(f"❌ PRODUCT FAILED: {url} - Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ PRODUCT ERROR: {url} - {str(e)}")
            return False

def run_tests():
    tester = QuickTester()
    
    # Load priority categories
    with open('priority_categories.json', 'r') as f:
        categories = json.load(f)
    
    logger.info("🧪 TESTING SCRAPING CAPABILITIES")
    logger.info("=" * 50)
    
    successful_categories = []
    
    # Test a few categories
    test_categories = ['rings', 'necklaces', 'earrings']
    
    for category in test_categories:
        if category in categories:
            logger.info(f"\n🔍 Testing category: {category.upper()}")
            category_urls = categories[category][:2]  # Test first 2 URLs
            
            for url in category_urls:
                success, product_links = tester.test_category_access(url)
                if success:
                    successful_categories.append(category)
                    
                    # Test one product page
                    if product_links:
                        logger.info(f"   🧪 Testing product page...")
                        tester.test_product_page(product_links[0])
                
                time.sleep(2)  # Be respectful
    
    logger.info(f"\n📊 TEST RESULTS:")
    logger.info(f"✅ Successful categories: {len(set(successful_categories))}")
    logger.info(f"📋 Categories tested: {len(test_categories)}")
    
    if successful_categories:
        logger.info("🚀 Ready to start full scraping!")
        return True
    else:
        logger.info("❌ Need to adjust scraping strategy")
        return False

if __name__ == "__main__":
    run_tests()

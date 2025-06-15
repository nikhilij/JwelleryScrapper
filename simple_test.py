"""
Simple working example of the PC Jewellers scraper.
This demonstrates the basic functionality with limited scraping.
"""

from pc_jewellers_scraper_selenium import PCJewellersScraper
from config import CATEGORIES

def run_simple_test():
    """Run a simple test with one category and few products."""
    print("🚀 PC Jewellers Scraper - Simple Test")
    print("=" * 50)
    
    # Create scraper instance
    scraper = PCJewellersScraper()
    
    # Modify config for testing
    from config import SCRAPING_CONFIG
    original_limit = SCRAPING_CONFIG["max_products_per_category"]
    original_headless = SCRAPING_CONFIG["headless"]
      # Set limits for testing
    SCRAPING_CONFIG["max_products_per_category"] = 3  # Only 3 products
    SCRAPING_CONFIG["headless"] = True  # Run in background
    
    try:
        print("🔧 Testing with first category only...")
        test_category = CATEGORIES[0]  # Just test rings
        
        print(f"📦 Scraping category: {test_category['name']}")
        
        # Initialize the driver
        scraper.driver = scraper.create_driver()
        
        try:
            products = scraper.scrape_category(test_category)
            
            print(f"✅ Successfully scraped {len(products)} products!")
            
            if products:
                print("\n📋 Sample product data:")
                sample = products[0]
                for key, value in sample.items():
                    print(f"  {key}: {str(value)[:60]}...")
            
            # Save the test data
            scraper.scraped_data = products
            scraper.session_stats["end_time"] = scraper.session_stats["start_time"]  # Fix for summary
            scraper.save_data()
            scraper.print_summary()
            
            return len(products) > 0
            
        finally:
            # Always quit the driver
            if scraper.driver:
                scraper.driver.quit()
        
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
        return False
    
    finally:
        # Restore original settings
        SCRAPING_CONFIG["max_products_per_category"] = original_limit
        SCRAPING_CONFIG["headless"] = original_headless

if __name__ == "__main__":
    run_simple_test()

"""
Quick test of the enhanced scraper with metal type and weight extraction.
"""

from pc_jewellers_scraper_selenium import PCJewellersScraper
from config import CATEGORIES, SCRAPING_CONFIG

def test_enhanced_scraper():
    """Test the enhanced scraper with new fields."""
    print("🚀 Testing Enhanced PC Jewellers Scraper")
    print("=" * 60)
    
    # Create scraper instance
    scraper = PCJewellersScraper()
    
    # Modify config for quick testing
    original_limit = SCRAPING_CONFIG["max_products_per_category"]
    original_headless = SCRAPING_CONFIG["headless"]
    
    try:
        # Set limits for testing
        SCRAPING_CONFIG["max_products_per_category"] = 5  # Just 5 products for testing
        SCRAPING_CONFIG["headless"] = True  # Run in background
        
        print("🔧 Testing with first category only...")
        test_category = CATEGORIES[0]  # Just test rings
        
        print(f"📦 Scraping category: {test_category['name']}")
        
        # Initialize the driver
        scraper.driver = scraper.create_driver()
        
        try:
            products = scraper.scrape_category(test_category)
            
            print(f"✅ Successfully scraped {len(products)} products!")
            
            if products:
                print("\n📋 Sample product data with new fields:")
                sample = products[0]
                for key, value in sample.items():
                    print(f"  {key}: {str(value)[:80]}...")
                
                # Check if we have the new fields
                if 'metal_type' in sample:
                    print(f"\n✅ Metal type extraction working: {sample['metal_type']}")
                if 'weight' in sample:
                    print(f"✅ Weight extraction working: {sample['weight']}")
            
            # Save the test data
            scraper.scraped_data = products
            scraper.session_stats["end_time"] = scraper.session_stats["start_time"]  # Fix for summary
            scraper.save_data()
            
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
    test_enhanced_scraper()

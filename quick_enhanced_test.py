"""
Run the enhanced scraper with limited products to test new features.
"""

from pc_jewellers_scraper_selenium import PCJewellersScraper
from config import SCRAPING_CONFIG

def run_enhanced_test():
    """Run enhanced scraper with limited products."""
    print("🚀 Enhanced PC Jewellers Scraper - Limited Test")
    print("=" * 60)
    
    # Save original settings
    original_limit = SCRAPING_CONFIG["max_products_per_category"]
    
    try:
        # Set for testing - 10 products per category for ~50 total
        SCRAPING_CONFIG["max_products_per_category"] = 10
        
        scraper = PCJewellersScraper()
        scraper.scrape_all_categories()
        scraper.save_data()
        scraper.print_summary()
        
        # Quick analysis of results
        if scraper.scraped_data:
            print(f"\n📊 Enhanced Features Test:")
            sample = scraper.scraped_data[0]
            
            if 'metal_type' in sample:
                metals = set(item.get('metal_type', 'unknown') for item in scraper.scraped_data)
                print(f"✅ Metal types found: {', '.join(metals)}")
            
            if 'weight' in sample:
                weights = [item.get('weight', 'unknown') for item in scraper.scraped_data if item.get('weight', 'unknown') != 'unknown']
                print(f"✅ Weight info found in {len(weights)} products")
            
            urls = [item.get('product_url', '') for item in scraper.scraped_data if item.get('product_url', '')]
            print(f"✅ Product URLs found: {len(urls)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        # Restore original settings
        SCRAPING_CONFIG["max_products_per_category"] = original_limit

if __name__ == "__main__":
    run_enhanced_test()

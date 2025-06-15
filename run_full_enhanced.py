"""
Run the enhanced scraper to get around 150 products with metal types and weights.
"""

from pc_jewellers_scraper_selenium import PCJewellersScraper
from config import SCRAPING_CONFIG

def run_full_enhanced_scraper():
    """Run the enhanced scraper for 150 products."""
    print("🚀 Enhanced PC Jewellers Scraper - Full Run (150 Products)")
    print("=" * 70)
    
    # Save original settings
    original_limit = SCRAPING_CONFIG["max_products_per_category"]
    
    try:
        # Set for 150 products total (30 per category)
        SCRAPING_CONFIG["max_products_per_category"] = 30
        
        print(f"📊 Target: {SCRAPING_CONFIG['max_products_per_category']} products per category")
        print(f"📊 Expected total: ~{SCRAPING_CONFIG['max_products_per_category'] * 5} products")
        print("🔄 Starting enhanced scraping...")
        
        scraper = PCJewellersScraper()
        scraper.scrape_all_categories()
        scraper.save_data()
        scraper.print_summary()
        
        # Analyze enhanced features
        if scraper.scraped_data:
            print(f"\n🎯 Enhanced Features Analysis:")
            
            # Metal type analysis
            metals = {}
            weights_found = 0
            urls_found = 0
            
            for item in scraper.scraped_data:
                metal = item.get('metal_type', 'unknown')
                metals[metal] = metals.get(metal, 0) + 1
                
                if item.get('weight', 'unknown') != 'unknown':
                    weights_found += 1
                    
                if item.get('product_url', ''):
                    urls_found += 1
            
            print(f"✅ Metal types identified: {len(metals)} types")
            for metal, count in metals.items():
                percentage = (count / len(scraper.scraped_data)) * 100
                print(f"   {metal}: {count} products ({percentage:.1f}%)")
            
            print(f"✅ Weight information: {weights_found}/{len(scraper.scraped_data)} products ({weights_found/len(scraper.scraped_data)*100:.1f}%)")
            print(f"✅ Product URLs: {urls_found}/{len(scraper.scraped_data)} products ({urls_found/len(scraper.scraped_data)*100:.1f}%)")
            
            print(f"\n📁 Data files generated with enhanced structure:")
            print(f"   - Enhanced CSV with metal_type and weight columns")
            print(f"   - Enhanced JSON with complete product information")
            print(f"   - Analysis report with metal type breakdowns")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during enhanced scraping: {str(e)}")
        return False
    
    finally:
        # Restore original settings
        SCRAPING_CONFIG["max_products_per_category"] = original_limit

if __name__ == "__main__":
    success = run_full_enhanced_scraper()
    if success:
        print(f"\n🎉 Enhanced scraping completed successfully!")
        print(f"📊 Check the 'data' folder for enhanced results")
        print(f"🔍 Run data analysis: python data_analyzer.py data\\pc_jewellers_products_[timestamp].csv")
    else:
        print(f"\n❌ Enhanced scraping encountered issues")

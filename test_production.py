#!/usr/bin/env python3

import sys
import traceback

def test_production_scraper():
    try:
        print("🔄 Testing production scraper imports...")
        
        # Test basic imports
        import cloudscraper
        import json
        import os
        print("✅ Basic imports successful")
        
        # Test file existence
        if not os.path.exists('priority_categories.json'):
            print("❌ priority_categories.json not found!")
            return
        
        # Load categories
        with open('priority_categories.json', 'r') as f:
            categories = json.load(f)
        print(f"✅ Loaded {len(categories)} categories")
        
        # Import production scraper
        from production_scraper import ProductionScraper
        print("✅ ProductionScraper imported successfully")
        
        # Create scraper instance
        scraper = ProductionScraper(max_products_per_category=10)
        print("✅ Scraper instance created")
        
        # Test one category with limited products
        print("\n🔄 Testing with rings category (10 products max)...")
        category_name = "rings"
        category_urls = categories[category_name][:1]  # Just first URL
        
        products = scraper.scrape_category(category_name, category_urls)
        print(f"✅ Successfully scraped {len(products)} products")
        
        if products:
            # Save test results
            scraper.save_final_results(products)
            print("✅ Test results saved")
            
            # Show sample product
            sample = products[0]
            print(f"\n📦 Sample product:")
            print(f"   Name: {sample['name'][:50]}...")
            print(f"   Price: {sample['price']}")
            print(f"   Images: {len(sample['image_urls'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_production_scraper()
    if success:
        print("\n🎉 Test completed successfully!")
        print("Ready to run full production scraping.")
    else:
        print("\n💥 Test failed! Please fix issues before running production.")

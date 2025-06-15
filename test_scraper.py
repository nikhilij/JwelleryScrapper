"""
Quick test script to verify the PC Jewellers scraper setup and basic functionality.
"""

import sys
import logging
from pc_jewellers_scraper_selenium import PCJewellersScraper
from config import BASE_URL, CATEGORIES

def test_basic_setup():
    """Test basic scraper setup."""
    print("🔧 Testing basic scraper setup...")
    
    try:
        scraper = PCJewellersScraper()
        print("✅ Scraper initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Scraper initialization failed: {str(e)}")
        return False

def test_webdriver():
    """Test WebDriver creation."""
    print("🌐 Testing WebDriver setup...")
    
    try:
        scraper = PCJewellersScraper()
        driver = scraper.create_driver()
        
        # Test navigation to main page
        driver.get(BASE_URL)
        title = driver.title
        print(f"✅ WebDriver working. Page title: {title[:50]}...")
        
        driver.quit()
        return True
    except Exception as e:
        print(f"❌ WebDriver test failed: {str(e)}")
        return False

def test_single_category():
    """Test scraping a single category with limited products."""
    print("📦 Testing single category scraping...")
    
    try:
        scraper = PCJewellersScraper()
        
        # Modify config for testing - limit products
        from config import SCRAPING_CONFIG
        original_limit = SCRAPING_CONFIG["max_products_per_category"]
        SCRAPING_CONFIG["max_products_per_category"] = 5  # Limit to 5 products for testing
        
        # Test with first category
        test_category = CATEGORIES[0]
        print(f"Testing category: {test_category['name']}")
        
        products = scraper.scrape_category(test_category)
        
        print(f"✅ Scraped {len(products)} products from {test_category['name']}")
        
        if products:
            sample_product = products[0]
            print("Sample product:")
            for key, value in sample_product.items():
                print(f"  {key}: {str(value)[:50]}...")
        
        # Restore original limit
        SCRAPING_CONFIG["max_products_per_category"] = original_limit
        
        return len(products) > 0
        
    except Exception as e:
        print(f"❌ Category scraping test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all tests."""
    print("🚀 PC Jewellers Scraper Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Setup", test_basic_setup),
        ("WebDriver", test_webdriver),
        ("Single Category", test_single_category)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name} Test:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The scraper is ready to use.")
        print("\nNext steps:")
        print("1. Run the full scraper: python pc_jewellers_scraper_selenium.py")
        print("2. Check the 'data' folder for scraped results")
        print("3. Use data_analyzer.py to analyze the results")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.WARNING)  # Reduce log noise during testing
    
    success = run_all_tests()
    sys.exit(0 if success else 1)

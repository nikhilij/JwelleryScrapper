import cloudscraper
import time

def simple_test():
    print("🧪 Simple CloudScraper Test")
    print("=" * 30)
    
    # Create scraper
    scraper = cloudscraper.create_scraper()
    
    # Test URL
    test_url = "https://www.pcjeweller.com/jewellery/rings.html"
    
    try:
        print(f"🔍 Testing: {test_url}")
        response = scraper.get(test_url, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! Bot protection bypassed!")
            
            # Check if it's the actual page (not a block page)
            if "jewellery" in response.text.lower() or "ring" in response.text.lower():
                print("✅ Got actual jewelry content!")
                return True
            else:
                print("❌ Got blocked or redirect page")
                return False
        else:
            print(f"❌ Failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = simple_test()
    if success:
        print("\n🚀 Ready to proceed with full scraping!")
    else:
        print("\n⚠️  Need alternative approach")

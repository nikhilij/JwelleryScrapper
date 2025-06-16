import cloudscraper
from bs4 import BeautifulSoup
import json

def diagnose_page_structure():
    """Analyze the actual page structure to find the correct selectors"""
    
    # Create CloudScraper session
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'linux', 'desktop': True}
    )
    
    # Test URL
    test_url = "https://www.pcjeweller.com/jewellery/rings.html"
    
    print(f"🔍 Analyzing page structure: {test_url}")
    print("=" * 60)
    
    try:
        response = scraper.get(test_url, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            print(f"✅ Page loaded successfully!")
            print(f"Title: {soup.find('title').text if soup.find('title') else 'No title'}")
            print(f"Content length: {len(response.content)} bytes")
            
            # Save the HTML for inspection
            with open('page_source.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("📄 Saved page source to 'page_source.html'")
            
            # Look for common patterns
            print("\n🔍 ANALYZING LINK PATTERNS:")
            print("-" * 40)
            
            # Find all links
            all_links = soup.find_all('a', href=True)
            print(f"Total links found: {len(all_links)}")
            
            # Analyze link patterns
            product_patterns = []
            jewelry_links = []
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if any(keyword in href.lower() for keyword in ['product', 'jewellery', 'jewelry', 'ring']):
                    if href.startswith('/'):
                        href = f"https://www.pcjeweller.com{href}"
                    jewelry_links.append({
                        'href': href,
                        'text': text,
                        'class': link.get('class', [])
                    })
            
            print(f"Jewelry-related links found: {len(jewelry_links)}")
            
            # Show sample links
            print("\n📋 SAMPLE JEWELRY LINKS:")
            for i, link in enumerate(jewelry_links[:10]):
                print(f"{i+1}. {link['href']}")
                print(f"   Text: {link['text']}")
                print(f"   Classes: {link['class']}")
                print()
            
            # Look for common HTML structures
            print("\n🔍 ANALYZING HTML STRUCTURE:")
            print("-" * 40)
            
            # Look for product containers
            container_selectors = [
                '.product', '.item', '.card', '.grid-item',
                '[class*="product"]', '[class*="item"]', '[class*="card"]'
            ]
            
            for selector in container_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    
                    # Show first element structure
                    if elements:
                        first_elem = elements[0]
                        print(f"   Sample element classes: {first_elem.get('class', [])}")
                        
                        # Look for links in this container
                        container_links = first_elem.find_all('a', href=True)
                        if container_links:
                            print(f"   Contains {len(container_links)} links")
                            for link in container_links[:2]:
                                print(f"      - {link.get('href')} ({link.get_text(strip=True)[:30]}...)")
                        print()
            
            # Look for pagination
            print("\n🔍 PAGINATION ANALYSIS:")
            print("-" * 30)
            pagination_selectors = [
                '.pagination', '.pager', '[class*="page"]', 
                'a[href*="page"]', 'nav[class*="page"]'
            ]
            
            for selector in pagination_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"Pagination found with selector: {selector}")
                    for elem in elements[:3]:
                        print(f"   Classes: {elem.get('class', [])}")
                        links = elem.find_all('a', href=True)
                        if links:
                            print(f"   Contains {len(links)} page links")
            
            # Look for JavaScript-loaded content indicators
            print("\n🔍 JAVASCRIPT CONTENT ANALYSIS:")
            print("-" * 35)
            
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and any(keyword in script.string.lower() for keyword in ['product', 'json', 'api']):
                    print("Found potential JavaScript data loading")
                    print(f"   Script content preview: {script.string[:200]}...")
                    break
            
            # Look for AJAX endpoints
            if 'ajax' in response.text.lower() or 'api' in response.text.lower():
                print("Page may use AJAX for dynamic content loading")
            
            # Save analysis results
            analysis = {
                'total_links': len(all_links),
                'jewelry_links': len(jewelry_links),
                'sample_links': jewelry_links[:5],
                'containers_found': [],
                'page_title': soup.find('title').text if soup.find('title') else None
            }
            
            with open('page_analysis.json', 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            print("\n💾 Analysis saved to 'page_analysis.json'")
            
            return jewelry_links
            
        else:
            print(f"❌ Failed to load page: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error analyzing page: {str(e)}")
        return []

if __name__ == "__main__":
    links = diagnose_page_structure()
    
    if links:
        print(f"\n🎯 RESULT: Found {len(links)} potential product links")
        print("📄 Check 'page_source.html' and 'page_analysis.json' for detailed analysis")
    else:
        print("\n❌ No product links found - check page structure")

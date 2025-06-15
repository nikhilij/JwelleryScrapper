"""
Interactive tool for testing and fine-tuning scraper selectors.
Useful for adapting the scraper to changes in website structure.
"""

import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from config import BASE_URL, SELECTORS, USER_AGENTS
import random


class SelectorTester:
    """Test and validate CSS selectors on the target website."""
    
    def __init__(self):
        self.test_results = {}
    
    async def test_selectors_on_page(self, url: str, selectors: dict):
        """Test all selectors on a specific page."""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1920, "height": 1080}
            )
            
            page = await context.new_page()
            
            try:
                print(f"\nTesting selectors on: {url}")
                await page.goto(url, wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                html_content = await page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                results = {}
                
                for selector_name, selector in selectors.items():
                    elements = soup.select(selector)
                    results[selector_name] = {
                        "selector": selector,
                        "found_count": len(elements),
                        "success": len(elements) > 0,
                        "sample_text": elements[0].get_text(strip=True)[:100] if elements else None
                    }
                    
                    print(f"  {selector_name}: {len(elements)} elements found")
                    if elements:
                        print(f"    Sample: {elements[0].get_text(strip=True)[:50]}...")
                
                return results
                
            finally:
                await browser.close()
    
    async def find_product_containers(self, category_url: str):
        """Automatically find potential product container selectors."""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1920, "height": 1080}
            )
            
            page = await context.new_page()
            
            try:
                print(f"\nAnalyzing page structure: {category_url}")
                await page.goto(category_url, wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                # Common product container patterns
                potential_selectors = [
                    "[data-product]",
                    "[data-product-id]", 
                    ".product",
                    ".product-item",
                    ".product-card",
                    ".item",
                    ".card",
                    ".grid-item",
                    ".product-tile",
                    ".product-list-item",
                    ".listing-item",
                    "article",
                    "[class*='product']",
                    "[class*='item']"
                ]
                
                html_content = await page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                print("\nTesting potential product container selectors:")
                candidates = []
                
                for selector in potential_selectors:
                    try:
                        elements = soup.select(selector)
                        if 5 <= len(elements) <= 100:  # Reasonable range for product containers
                            # Check if elements contain product-like content
                            sample_element = elements[0]
                            text_content = sample_element.get_text(strip=True).lower()
                            
                            # Look for price indicators
                            has_price = any(indicator in text_content for indicator in 
                                          ['$', '₹', 'price', 'cost', 'rs.', 'inr'])
                            
                            candidates.append({
                                "selector": selector,
                                "count": len(elements),
                                "has_price_indicator": has_price,
                                "sample_text": text_content[:100]
                            })
                            
                            print(f"  {selector}: {len(elements)} elements, price indicators: {has_price}")
                    
                    except Exception as e:
                        continue
                
                # Sort by likelihood (prefer selectors with price indicators and reasonable counts)
                candidates.sort(key=lambda x: (x['has_price_indicator'], -abs(x['count'] - 20)))
                
                return candidates[:5]  # Return top 5 candidates
                
            finally:
                await browser.close()
    
    async def test_data_extraction(self, category_url: str, product_selector: str):
        """Test data extraction with a specific product selector."""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1920, "height": 1080}
            )
            
            page = await context.new_page()
            
            try:
                await page.goto(category_url, wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                html_content = await page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                product_containers = soup.select(product_selector)
                print(f"\nTesting data extraction from {len(product_containers)} products:")
                
                # Test extraction selectors on first few products
                extraction_results = []
                
                for i, container in enumerate(product_containers[:3]):
                    print(f"\nProduct {i+1}:")
                    result = {"product_index": i+1}
                    
                    # Test name extraction
                    name_selectors = ["h1", "h2", "h3", "h4", ".title", ".name", ".product-name", ".product-title"]
                    for selector in name_selectors:
                        element = container.select_one(selector)
                        if element:
                            text = element.get_text(strip=True)
                            if text and len(text) > 5:
                                result["name"] = text
                                print(f"  Name ({selector}): {text[:50]}...")
                                break
                    
                    # Test price extraction
                    price_selectors = [".price", ".cost", ".amount", "[data-price]", ".product-price"]
                    for selector in price_selectors:
                        element = container.select_one(selector)
                        if element:
                            text = element.get_text(strip=True)
                            if any(char in text for char in ['$', '₹', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
                                result["price"] = text
                                print(f"  Price ({selector}): {text}")
                                break
                    
                    # Test image extraction
                    img_element = container.select_one("img")
                    if img_element:
                        img_src = img_element.get('src') or img_element.get('data-src')
                        if img_src:
                            result["image"] = img_src
                            print(f"  Image: {img_src[:50]}...")
                    
                    # Test link extraction
                    link_element = container.select_one("a")
                    if link_element:
                        href = link_element.get('href')
                        if href:
                            result["link"] = href
                            print(f"  Link: {href[:50]}...")
                    
                    extraction_results.append(result)
                
                return extraction_results
                
            finally:
                await browser.close()
    
    def save_test_results(self, results: dict, filename: str = "selector_test_results.json"):
        """Save test results to file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nTest results saved to {filename}")


async def interactive_selector_testing():
    """Interactive tool for testing selectors."""
    tester = SelectorTester()
    
    print("PC Jewellers Selector Testing Tool")
    print("=" * 40)
    
    # Test main page selectors
    print("\n1. Testing current selectors on main page...")
    main_results = await tester.test_selectors_on_page(BASE_URL, SELECTORS)
    
    # Find potential product containers
    print("\n2. Analyzing potential product containers...")
    category_url = f"{BASE_URL}/rings"  # Test with rings category
    containers = await tester.find_product_containers(category_url)
    
    if containers:
        print(f"\nFound {len(containers)} potential product container selectors:")
        for i, container in enumerate(containers):
            print(f"{i+1}. {container['selector']} ({container['count']} elements)")
        
        # Test extraction with best candidate
        best_selector = containers[0]['selector']
        print(f"\n3. Testing data extraction with: {best_selector}")
        extraction_results = await tester.test_data_extraction(category_url, best_selector)
        
        # Save results
        all_results = {
            "main_page_selectors": main_results,
            "product_containers": containers,
            "extraction_test": extraction_results,
            "recommended_selector": best_selector
        }
        
        tester.save_test_results(all_results)
        
        print(f"\n" + "="*50)
        print("RECOMMENDATIONS:")
        print(f"  Best product container selector: {best_selector}")
        print(f"  Found {containers[0]['count']} products with this selector")
        print(f"  Has price indicators: {containers[0]['has_price_indicator']}")
        print("="*50)
    
    else:
        print("No suitable product containers found. The website structure may have changed.")


async def quick_selector_test():
    """Quick test of current selectors."""
    tester = SelectorTester()
    
    test_urls = [
        BASE_URL,
        f"{BASE_URL}/rings",
        f"{BASE_URL}/bracelets"
    ]
    
    for url in test_urls:
        try:
            results = await tester.test_selectors_on_page(url, SELECTORS)
            
            # Check if any selectors found products
            product_selector_working = results.get("product_container", {}).get("success", False)
            
            if product_selector_working:
                print(f"✅ Selectors working on {url}")
            else:
                print(f"❌ Product selector not working on {url}")
                
        except Exception as e:
            print(f"❌ Error testing {url}: {str(e)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        asyncio.run(quick_selector_test())
    else:
        asyncio.run(interactive_selector_testing())

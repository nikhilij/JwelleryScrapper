import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import time

def simple_scraper():
    """Simple scraper that tries different approaches"""
    
    url = "https://www.pcjeweller.com/all-jewellery.html"
    base_url = "https://www.pcjeweller.com"
    
    print(f"Attempting to scrape: {url}")
    print("=" * 60)
    
    # Try different approaches
    approaches = [
        {
            'name': 'Minimal Headers',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            }
        },
        {
            'name': 'Standard Browser Headers',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
        },
        {
            'name': 'Mobile User Agent',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
            }
        }
    ]
    
    for approach in approaches:
        print(f"\nTrying approach: {approach['name']}")
        try:
            response = requests.get(url, headers=approach['headers'], timeout=30)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                print("Success! Parsing content...")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all links
                links = soup.find_all('a', href=True)
                
                extracted_links = []
                unique_links = set()
                
                for link in links:
                    href = link['href'].strip()
                    
                    # Skip unwanted links
                    if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                        continue
                    
                    # Convert to absolute URL
                    if href.startswith('/'):
                        full_url = urljoin(base_url, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(url, href)
                    
                    # Add unique links
                    if full_url not in unique_links:
                        unique_links.add(full_url)
                        
                        link_text = link.get_text(strip=True)
                        
                        extracted_links.append({
                            'url': full_url,
                            'text': link_text,
                            'title': link.get('title', ''),
                            'class': link.get('class', [])
                        })
                
                if extracted_links:
                    print(f"Found {len(extracted_links)} unique links")
                    
                    # Save to files
                    with open('simple_scraper_links.json', 'w', encoding='utf-8') as f:
                        json.dump(extracted_links, f, indent=2, ensure_ascii=False)
                    
                    with open('simple_scraper_links.txt', 'w', encoding='utf-8') as f:
                        for link in extracted_links:
                            f.write(f"{link['url']}\n")
                    
                    print("Links saved to 'simple_scraper_links.json' and 'simple_scraper_links.txt'")
                    
                    # Show sample
                    print("\nFirst 10 links:")
                    print("-" * 40)
                    for i, link in enumerate(extracted_links[:10]):
                        print(f"{i+1}. {link['url']}")
                        if link['text']:
                            print(f"   Text: {link['text'][:50]}...")
                        print()
                    
                    return extracted_links
                else:
                    print("No links found in the page")
            
            elif response.status_code == 403:
                print("Access forbidden (403)")
            else:
                print(f"Unexpected status code: {response.status_code}")
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            
        time.sleep(2)  # Wait between attempts
    
    print("\nAll approaches failed. The website may have strong anti-bot protection.")
    
    # Try to get the robots.txt to understand the site's policy
    try:
        print("\nChecking robots.txt...")
        robots_url = urljoin(base_url, '/robots.txt')
        robots_response = requests.get(robots_url, timeout=10)
        if robots_response.status_code == 200:
            print("Robots.txt content:")
            print(robots_response.text[:500])
        else:
            print(f"Robots.txt not accessible (status: {robots_response.status_code})")
    except:
        print("Could not fetch robots.txt")
    
    return []

if __name__ == "__main__":
    links = simple_scraper()
    if links:
        print(f"\nScraping completed successfully! Found {len(links)} links.")
    else:
        print("\nScraping failed. No links extracted.")

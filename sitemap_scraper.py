import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import json
import time

def scrape_sitemap():
    """Scrape links from the sitemap which is usually publicly accessible"""
    
    sitemap_url = "https://www.pcjeweller.com/sitemap.xml"
    base_url = "https://www.pcjeweller.com"
    
    print(f"Attempting to scrape sitemap: {sitemap_url}")
    print("=" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(sitemap_url, headers=headers, timeout=30)
        print(f"Sitemap status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Successfully fetched sitemap!")
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Handle different sitemap formats
            namespaces = {
                'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                'xhtml': 'http://www.w3.org/1999/xhtml'
            }
            
            extracted_links = []
            
            # Look for URL elements in sitemap
            for url_elem in root.findall('.//sitemap:url', namespaces):
                loc_elem = url_elem.find('sitemap:loc', namespaces)
                if loc_elem is not None:
                    url = loc_elem.text.strip()
                    
                    # Get additional metadata if available
                    lastmod_elem = url_elem.find('sitemap:lastmod', namespaces)
                    changefreq_elem = url_elem.find('sitemap:changefreq', namespaces)
                    priority_elem = url_elem.find('sitemap:priority', namespaces)
                    
                    link_info = {
                        'url': url,
                        'lastmod': lastmod_elem.text if lastmod_elem is not None else '',
                        'changefreq': changefreq_elem.text if changefreq_elem is not None else '',
                        'priority': priority_elem.text if priority_elem is not None else '',
                        'source': 'sitemap'
                    }
                    
                    extracted_links.append(link_info)
            
            # If no URLs found with namespace, try without namespace
            if not extracted_links:
                print("No URLs found with namespace, trying without namespace...")
                for url_elem in root.findall('.//url'):
                    loc_elem = url_elem.find('loc')
                    if loc_elem is not None:
                        url = loc_elem.text.strip()
                        extracted_links.append({
                            'url': url,
                            'source': 'sitemap'
                        })
            
            # Check for sitemap index (multiple sitemaps)
            if not extracted_links:
                print("Checking for sitemap index...")
                for sitemap_elem in root.findall('.//sitemap:sitemap', namespaces):
                    loc_elem = sitemap_elem.find('sitemap:loc', namespaces)
                    if loc_elem is not None:
                        sub_sitemap_url = loc_elem.text.strip()
                        print(f"Found sub-sitemap: {sub_sitemap_url}")
                        
                        # Fetch sub-sitemap
                        try:
                            sub_response = requests.get(sub_sitemap_url, headers=headers, timeout=30)
                            if sub_response.status_code == 200:
                                sub_root = ET.fromstring(sub_response.content)
                                
                                for url_elem in sub_root.findall('.//sitemap:url', namespaces):
                                    loc_elem = url_elem.find('sitemap:loc', namespaces)
                                    if loc_elem is not None:
                                        url = loc_elem.text.strip()
                                        extracted_links.append({
                                            'url': url,
                                            'source': f'sub-sitemap: {sub_sitemap_url}'
                                        })
                                        
                        except Exception as e:
                            print(f"Error fetching sub-sitemap {sub_sitemap_url}: {e}")
            
            if extracted_links:
                print(f"Found {len(extracted_links)} URLs in sitemap(s)")
                
                # Filter for jewellery-related URLs
                jewellery_links = []
                jewellery_keywords = ['jewellery', 'jewelry', 'ring', 'necklace', 'earring', 'bracelet', 
                                    'pendant', 'gold', 'diamond', 'silver', 'product', 'collection']
                
                for link in extracted_links:
                    url_lower = link['url'].lower()
                    if any(keyword in url_lower for keyword in jewellery_keywords):
                        jewellery_links.append(link)
                
                print(f"Found {len(jewellery_links)} jewellery-related URLs")
                
                # Save all links
                with open('sitemap_all_links.json', 'w', encoding='utf-8') as f:
                    json.dump(extracted_links, f, indent=2, ensure_ascii=False)
                
                with open('sitemap_all_links.txt', 'w', encoding='utf-8') as f:
                    for link in extracted_links:
                        f.write(f"{link['url']}\n")
                
                # Save jewellery links
                if jewellery_links:
                    with open('sitemap_jewellery_links.json', 'w', encoding='utf-8') as f:
                        json.dump(jewellery_links, f, indent=2, ensure_ascii=False)
                    
                    with open('sitemap_jewellery_links.txt', 'w', encoding='utf-8') as f:
                        for link in jewellery_links:
                            f.write(f"{link['url']}\n")
                
                print("Links saved to sitemap_*_links.json and sitemap_*_links.txt files")
                
                # Show sample
                print("\nSample URLs (first 10):")
                print("-" * 50)
                for i, link in enumerate(extracted_links[:10]):
                    print(f"{i+1}. {link['url']}")
                
                if len(extracted_links) > 10:
                    print(f"... and {len(extracted_links) - 10} more URLs")
                
                return extracted_links
            else:
                print("No URLs found in sitemap")
                
                # Print raw XML for debugging
                print("\nRaw XML (first 1000 chars):")
                print(response.text[:1000])
                
        else:
            print(f"Failed to fetch sitemap. Status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return []

def try_alternative_pages():
    """Try to access some common pages that might be less protected"""
    
    base_url = "https://www.pcjeweller.com"
    test_urls = [
        "/",
        "/about",
        "/contact",
        "/collections",
        "/categories"
    ]
    
    print("\nTrying alternative pages...")
    print("-" * 40)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    }
    
    accessible_pages = []
    
    for path in test_urls:
        url = urljoin(base_url, path)
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"{url}: {response.status_code}")
            if response.status_code == 200:
                accessible_pages.append(url)
        except Exception as e:
            print(f"{url}: Error - {e}")
    
    return accessible_pages

if __name__ == "__main__":
    print("PC Jeweller Sitemap Scraper")
    print("=" * 60)
    
    # Try sitemap first
    links = scrape_sitemap()
    
    # Try alternative pages
    accessible = try_alternative_pages()
    
    if links:
        print(f"\nScraping completed successfully! Found {len(links)} links from sitemap.")
    else:
        print("\nSitemap scraping failed.")
    
    if accessible:
        print(f"Found {len(accessible)} accessible pages that could be scraped individually.")
    else:
        print("No alternative pages found accessible.")

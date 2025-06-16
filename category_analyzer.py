import json
import re
from urllib.parse import urlparse
from collections import defaultdict, Counter
import pandas as pd

class CategoryAnalyzer:
    def __init__(self, links_file="pcjeweller_links.json"):
        self.links_file = links_file
        self.categories = defaultdict(list)
        self.jewelry_categories = {}
        
    def analyze_links(self):
        """Analyze and categorize all links"""
        print("🔍 Analyzing links from pcjeweller_links.json...")
        
        try:
            with open(self.links_file, 'r', encoding='utf-8') as f:
                links_data = json.load(f)
        except Exception as e:
            print(f"❌ Error loading links file: {str(e)}")
            return
        
        # Categorize links
        jewelry_links = []
        other_links = []
        
        for link_data in links_data:
            url = link_data['url']
            text = link_data.get('text', '')
            
            # Skip non-HTTP links
            if not url.startswith('http'):
                continue
                
            # Analyze URL structure
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            if '/jewellery/' in path:
                jewelry_links.append({
                    'url': url,
                    'text': text,
                    'path': path
                })
            else:
                other_links.append({
                    'url': url,
                    'text': text,
                    'path': path
                })
        
        print(f"📦 Found {len(jewelry_links)} jewelry-related links")
        print(f"🔗 Found {len(other_links)} other links")
        
        return self.categorize_jewelry_links(jewelry_links)
    
    def categorize_jewelry_links(self, jewelry_links):
        """Categorize jewelry links by type"""
        categories = {
            'rings': [],
            'necklaces': [],
            'earrings': [],
            'bracelets': [],
            'bangles': [],
            'pendants': [],
            'chains': [],
            'sets': [],
            'mens': [],
            'collections': [],
            'others': []
        }
        
        # Category keywords mapping
        category_keywords = {
            'rings': ['ring', 'band', 'engagement', 'wedding', 'solitaire', 'cocktail'],
            'necklaces': ['necklace', 'choker', 'collar'],
            'earrings': ['earring', 'stud', 'hoop', 'drop', 'dangle'],
            'bracelets': ['bracelet', 'bangle', 'kada'],
            'bangles': ['bangle', 'kada', 'bracelet'],
            'pendants': ['pendant', 'locket'],
            'chains': ['chain', 'mangalsutra'],
            'sets': ['set', 'combo', 'complete'],
            'mens': ['men', 'male', 'gents'],
            'collections': ['collection', 'designer', 'premium', 'luxury']
        }
        
        for link in jewelry_links:
            url = link['url'].lower()
            text = link['text'].lower()
            path = link['path']
            
            categorized = False
            
            # Check each category
            for category, keywords in category_keywords.items():
                if any(keyword in url or keyword in text for keyword in keywords):
                    categories[category].append(link)
                    categorized = True
                    break
            
            if not categorized:
                categories['others'].append(link)
        
        # Print category summary
        print("\n📊 JEWELRY CATEGORIES ANALYSIS")
        print("=" * 50)
        
        total_products_estimate = 0
        for category, links in categories.items():
            if links:
                print(f"🏷️  {category.title()}: {len(links)} category pages")
                # Estimate products (assuming 50-150 products per category page)
                estimated_products = len(links) * 100
                total_products_estimate += estimated_products
                print(f"   📦 Estimated products: ~{estimated_products}")
                print(f"   🔗 Sample links:")
                for link in links[:3]:
                    print(f"      - {link['url']}")
                print()
        
        print(f"🎯 TOTAL ESTIMATED PRODUCTS: ~{total_products_estimate}")
        print(f"📈 With 150 products per category limit: ~{len([l for links in categories.values() for l in links]) * 150}")
        
        # Save category analysis
        self.save_category_analysis(categories)
        
        return categories
    
    def save_category_analysis(self, categories):
        """Save category analysis to files"""
        # Save as JSON
        with open('category_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(categories, f, indent=2, ensure_ascii=False)
        
        # Save as CSV for easy viewing
        csv_data = []
        for category, links in categories.items():
            for link in links:
                csv_data.append({
                    'category': category,
                    'url': link['url'],
                    'text': link['text'],
                    'path': link['path']
                })
        
        df = pd.DataFrame(csv_data)
        df.to_csv('category_analysis.csv', index=False)
        
        # Save priority categories (most promising for scraping)
        priority_categories = {}
        for category, links in categories.items():
            if len(links) > 0 and category != 'others':
                priority_categories[category] = [link['url'] for link in links]
        
        with open('priority_categories.json', 'w', encoding='utf-8') as f:
            json.dump(priority_categories, f, indent=2, ensure_ascii=False)
        
        print("💾 Saved analysis files:")
        print("   - category_analysis.json")
        print("   - category_analysis.csv")
        print("   - priority_categories.json")
    
    def create_scraping_plan(self):
        """Create a detailed scraping plan"""
        categories = self.analyze_links()
        
        print("\n🎯 RECOMMENDED SCRAPING PLAN")
        print("=" * 50)
        
        # Priority order based on typical jewelry popularity
        priority_order = [
            'rings', 'necklaces', 'earrings', 'bracelets', 
            'pendants', 'chains', 'sets', 'bangles', 'mens', 'collections'
        ]
        
        total_estimated_time = 0
        
        for i, category in enumerate(priority_order, 1):
            if category in categories and categories[category]:
                links_count = len(categories[category])
                estimated_products = min(links_count * 150, links_count * 100)  # Conservative estimate
                estimated_time = estimated_products * 0.1  # 0.1 minutes per product
                total_estimated_time += estimated_time
                
                print(f"{i}. {category.upper()}")
                print(f"   📁 Category pages: {links_count}")
                print(f"   📦 Estimated products: ~{estimated_products}")
                print(f"   ⏱️  Estimated time: {estimated_time:.1f} minutes")
                print(f"   🔗 Sample URL: {categories[category][0]['url']}")
                print()
        
        print(f"🕐 TOTAL ESTIMATED TIME: {total_estimated_time:.1f} minutes ({total_estimated_time/60:.1f} hours)")
        print(f"💾 Estimated storage: ~{total_estimated_time * 10:.0f} MB (images + data)")
        
        return categories

if __name__ == "__main__":
    analyzer = CategoryAnalyzer()
    analyzer.create_scraping_plan()

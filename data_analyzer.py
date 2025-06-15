"""
Data analysis utilities for scraped jewelry data.
"""

import json
import csv
from typing import Dict, List, Optional
import re
from collections import Counter
import logging
from datetime import datetime


class JewelryDataAnalyzer:
    """Analyze scraped jewelry data and generate insights."""
    
    def __init__(self, data_path: str):
        """
        Initialize analyzer with data file.
        
        Args:
            data_path: Path to CSV or JSON file containing scraped data
        """
        self.data_path = data_path
        self.data = []
        self.load_data()
    
    def load_data(self):
        """Load data from file."""
        try:
            if self.data_path.endswith('.csv'):
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.data = list(reader)
            elif self.data_path.endswith('.json'):
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                raise ValueError("Unsupported file format. Use CSV or JSON.")
            
            logging.info(f"Loaded {len(self.data)} products from {self.data_path}")
            
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            raise
    
    def clean_price_data(self):
        """Clean and convert price data to numeric format."""
        def extract_price(price_str):
            if not price_str or price_str == "N/A":            return None
            
            # Remove currency symbols and commas
            price_clean = re.sub(r'[^\d.]', '', str(price_str))
            
            try:
                return float(price_clean) if price_clean else None
            except ValueError:
                return None
        
        for item in self.data:
            if 'price' in item:
                item['price_numeric'] = extract_price(item['price'])
        
        valid_prices = sum(1 for item in self.data if item.get('price_numeric') is not None)
        logging.info(f"Extracted {valid_prices} valid prices from {len(self.data)} products")
    
    def get_basic_stats(self) -> Dict:
        """Get basic statistics about the dataset."""
        if not self.data:
            return {}
        
        # Count categories
        categories = {}
        for item in self.data:
            cat = item.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        # Count metal types
        metal_types = {}
        for item in self.data:
            metal = item.get('metal_type', 'unknown')
            metal_types[metal] = metal_types.get(metal, 0) + 1
        
        stats = {
            "total_products": len(self.data),
            "categories": categories,
            "metal_types": metal_types,
            "products_with_prices": sum(1 for item in self.data if item.get('price') and item.get('price') != 'N/A'),
            "products_with_images": sum(1 for item in self.data if item.get('image_url')),
            "products_with_urls": sum(1 for item in self.data if item.get('product_url')),
            "products_with_metal_type": sum(1 for item in self.data if item.get('metal_type') and item.get('metal_type') != 'unknown'),
            "products_with_weight": sum(1 for item in self.data if item.get('weight') and item.get('weight') != 'unknown')
        }
        
        # Price statistics
        prices = [item.get('price_numeric') for item in self.data if item.get('price_numeric') is not None]
        if prices:
            stats["price_stats"] = {
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": sum(prices) / len(prices),
                "median_price": sorted(prices)[len(prices) // 2]
            }
        
        return stats
    
    def get_category_analysis(self) -> Dict:
        """Analyze products by category."""
        category_stats = {}
        
        # Group by category
        categories = {}
        for item in self.data:
            cat = item.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        
        for category, items in categories.items():
            stats = {
                "product_count": len(items),
                "percentage": (len(items) / len(self.data)) * 100
            }
            
            # Price analysis for category
            prices = [item.get('price_numeric') for item in items if item.get('price_numeric') is not None]
            if prices:
                stats["price_stats"] = {
                    "min_price": min(prices),
                    "max_price": max(prices),
                    "avg_price": sum(prices) / len(prices),
                    "products_with_price": len(prices)
                }
            
            category_stats[category] = stats
        
        return category_stats
    
    def find_price_outliers(self, threshold: float = 2.0) -> List[Dict]:
        """Find products with unusual prices."""
        prices = [item.get('price_numeric') for item in self.data if item.get('price_numeric') is not None]
        
        if len(prices) < 10:  # Need enough data for outlier detection
            return []
        
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        std_price = variance ** 0.5
        
        outliers = []
        for item in self.data:
            price = item.get('price_numeric')
            if price is not None and abs(price - mean_price) > (threshold * std_price):
                outliers.append({
                    'name': item.get('name', ''),
                    'price': item.get('price', ''),
                    'price_numeric': price,
                    'category': item.get('category', '')
                })
        
        return outliers
    
    def get_common_keywords(self, top_n: int = 20) -> List[tuple]:
        """Extract most common keywords from product names."""
        # Combine all product names
        all_names = ' '.join(item.get('name', '') for item in self.data).lower()
        
        # Extract words (remove common stop words)
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_names)
        words = [word for word in words if word not in stop_words]
        
        return Counter(words).most_common(top_n)
    
    def generate_report(self, output_path: str = None):
        """Generate a comprehensive analysis report."""
        self.clean_price_data()
        
        report = {
            "analysis_timestamp": str(datetime.now()),
            "data_source": self.data_path,
            "basic_stats": self.get_basic_stats(),
            "category_analysis": self.get_category_analysis(),
            "price_outliers": self.find_price_outliers(),
            "common_keywords": self.get_common_keywords()
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logging.info(f"Analysis report saved to {output_path}")
        
        return report


def analyze_data_file(file_path: str, output_dir: str = "analysis_output"):
    """
    Quick analysis function for a scraped data file.
    
    Args:
        file_path: Path to the data file
        output_dir: Directory to save analysis outputs
    """
    import os
    from datetime import datetime
    
    os.makedirs(output_dir, exist_ok=True)
    
    analyzer = JewelryDataAnalyzer(file_path)
    
    # Generate report
    report = analyzer.generate_report(f"{output_dir}/analysis_report.json")
      # Print summary
    stats = report["basic_stats"]
    print(f"\n{'='*50}")
    print("JEWELRY DATA ANALYSIS SUMMARY")
    print(f"{'='*50}")
    print(f"Total products: {stats['total_products']}")
    print(f"Categories: {len(stats['categories'])}")
    print(f"Products with prices: {stats['products_with_prices']}")
    print(f"Products with metal type: {stats.get('products_with_metal_type', 0)}")
    print(f"Products with weight: {stats.get('products_with_weight', 0)}")
    
    if "price_stats" in stats:
        price_stats = stats["price_stats"]
        print(f"Price range: ${price_stats['min_price']:.2f} - ${price_stats['max_price']:.2f}")
        print(f"Average price: ${price_stats['avg_price']:.2f}")
    
    print(f"\nCategory breakdown:")
    for category, count in stats['categories'].items():
        percentage = (count / stats['total_products']) * 100
        print(f"  {category}: {count} products ({percentage:.1f}%)")
    
    if 'metal_types' in stats:
        print(f"\nMetal type breakdown:")
        for metal, count in stats['metal_types'].items():
            percentage = (count / stats['total_products']) * 100
            print(f"  {metal}: {count} products ({percentage:.1f}%)")
    
    print(f"\nFull analysis saved to: {output_dir}/")
    print(f"{'='*50}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
        analyze_data_file(data_file)
    else:
        print("Usage: python data_analyzer.py <data_file.csv|data_file.json>")

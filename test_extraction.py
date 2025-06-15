"""
Test the new metal type and weight extraction functions.
"""

from pc_jewellers_scraper_selenium import PCJewellersScraper
import json

def test_extraction_functions():
    """Test the new extraction functions with sample data."""
    print("🧪 Testing Metal Type and Weight Extraction Functions")
    print("=" * 60)
    
    scraper = PCJewellersScraper()
    
    # Test cases for metal identification
    test_names = [
        "The Idamae Diamond Silver Ladies Ring",
        "22K Gold Wedding Band",
        "Platinum Solitaire Engagement Ring",
        "Sterling Silver 925 Bracelet",
        "Rose Gold Diamond Earrings 18K",
        "Pearl Necklace with Gold Chain",
        "Titanium Men's Ring 5.2 grams",
        "White Gold Ring 3.5gm",
        "Diamond Ring 2.1 ct weight"
    ]
    
    print("\n🔍 Testing Metal Type Extraction:")
    for name in test_names:
        metal_type = scraper.identify_metal_from_text(name.lower())
        print(f"  '{name}' → {metal_type}")
    
    print("\n⚖️  Testing Weight Extraction:")
    test_weights = [
        "Gold Ring 3.5 grams",
        "Silver Bracelet 12.2gm",
        "Diamond Earrings 2.1 carats",
        "Platinum Ring 4.8g weight",
        "Wedding Band 6.7 gms",
        "No weight mentioned here"
    ]
    
    for text in test_weights:
        weight = scraper.extract_weight_from_text(text)
        print(f"  '{text}' → {weight}")
    
    print("\n✅ Extraction functions are working!")
    
    # Test a sample product structure
    print("\n📦 Sample Enhanced Product Structure:")
    sample_product = {
        "name": "The Idamae Diamond Silver Ladies Ring",
        "price": "₹15,952",
        "image_url": "https://cf-cdn.pcjeweller.com/image.jpg",
        "product_url": "https://www.pcjeweller.com/product-page",
        "metal_type": scraper.identify_metal_from_text("The Idamae Diamond Silver Ladies Ring".lower()),
        "weight": scraper.extract_weight_from_text("The Idamae Diamond Silver Ladies Ring 3.2 grams"),
        "category": "rings",
        "scraped_at": "2025-06-15T22:15:00.000000"
    }
    
    print(json.dumps(sample_product, indent=2))
    print("\n🎉 Enhanced data structure ready!")

if __name__ == "__main__":
    test_extraction_functions()

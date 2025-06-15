"""
Complete PC Jewellers Scraper Setup and Demo
This script demonstrates all the features of the jewelry scraper.
"""

import os
import sys
import json
from datetime import datetime

def show_welcome():
    """Display welcome message and features."""
    print("🎉 PC Jewellers Scraper - Complete Setup")
    print("=" * 60)
    print("✨ Features:")
    print("  🤖 Selenium-based dynamic content scraping")
    print("  🛡️  Anti-bot protection with stealth mode")
    print("  📊 Data export to CSV and JSON")
    print("  🔍 Built-in data analysis tools")
    print("  ⚙️  Configurable scraping parameters")
    print("  🧪 Selector testing utilities")
    print()

def check_setup():
    """Check if the setup is complete."""
    print("🔧 Checking setup...")
    
    required_files = [
        "pc_jewellers_scraper_selenium.py",
        "config.py", 
        "utils.py",
        "data_analyzer.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    
    # Check if dependencies are installed
    try:
        import selenium
        import requests
        from bs4 import BeautifulSoup
        print("✅ Dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False

def show_usage_examples():
    """Show usage examples."""
    print("📚 Usage Examples:")
    print()
    
    examples = [
        {
            "title": "Quick Test (3 products)",
            "command": "python simple_test.py",
            "description": "Test scraper with limited products"
        },
        {
            "title": "Full Scraping",
            "command": "python pc_jewellers_scraper_selenium.py", 
            "description": "Scrape all categories completely"
        },
        {
            "title": "Analyze Data", 
            "command": "python data_analyzer.py data/pc_jewellers_products_*.csv",
            "description": "Analyze scraped data"
        },
        {
            "title": "Test Selectors",
            "command": "python selector_tester.py",
            "description": "Validate CSS selectors"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['title']}")
        print(f"   Command: {example['command']}")
        print(f"   Purpose: {example['description']}")
        print()

def show_configuration_tips():
    """Show configuration tips."""
    print("⚙️  Configuration Tips:")
    print()
    print("Edit config.py to customize:")
    print("  • SCRAPING_CONFIG['delay_between_requests'] - Speed control")
    print("  • SCRAPING_CONFIG['max_products_per_category'] - Limit products")
    print("  • SCRAPING_CONFIG['headless'] - Show/hide browser")
    print("  • CATEGORIES - Choose jewelry types to scrape")
    print("  • OUTPUT_CONFIG - Data export options")
    print()

def show_output_info():
    """Show output information."""
    print("📁 Output Information:")
    print()
    print("Data files saved to 'data/' directory:")
    print("  • pc_jewellers_products_TIMESTAMP.csv - Product data")
    print("  • pc_jewellers_products_TIMESTAMP.json - Same data in JSON")
    print("  • session_stats_TIMESTAMP.json - Scraping statistics")
    print()
    print("Log files saved to 'logs/' directory:")
    print("  • pc_jewellers_scraper_TIMESTAMP.log - Detailed logs")
    print()

def show_compliance_notes():
    """Show compliance and ethical notes."""
    print("⚖️  Compliance & Ethics:")
    print()
    print("✅ Built-in compliance features:")
    print("  • Respects robots.txt")
    print("  • Polite delays (1 request/second)")
    print("  • User agent rotation")
    print("  • Rate limiting protection")
    print()
    print("⚠️  Please remember:")
    print("  • Use responsibly and ethically")
    print("  • Don't overload the server")
    print("  • Check terms of service")
    print("  • Consider data usage rights")
    print()

def show_troubleshooting():
    """Show troubleshooting tips."""
    print("🔧 Troubleshooting:")
    print()
    
    issues = [
        {
            "problem": "ChromeDriver issues",
            "solution": "webdriver-manager will auto-install. Ensure Chrome browser is installed."
        },
        {
            "problem": "No products found",
            "solution": "Website structure may have changed. Run selector_tester.py to validate."
        },
        {
            "problem": "Timeout errors",
            "solution": "Increase timeout in config.py or check internet connection."
        },
        {
            "problem": "Anti-bot detection",
            "solution": "Increase delays, use headless=False, or rotate user agents."
        }
    ]
    
    for issue in issues:
        print(f"❓ {issue['problem']}")
        print(f"   💡 {issue['solution']}")
        print()

def create_demo_config():
    """Create a demo configuration file."""
    demo_config = {
        "demo_mode": True,
        "max_products": 5,
        "categories": ["rings"],
        "quick_test": True
    }
    
    with open("demo_config.json", "w") as f:
        json.dump(demo_config, f, indent=2)
    
    print("📝 Created demo_config.json for testing")

def main():
    """Main function."""
    show_welcome()
    
    if not check_setup():
        print("\n❌ Setup incomplete. Please install dependencies first.")
        return
    
    print("\n🎯 Ready to scrape! Choose your next step:")
    print()
    
    show_usage_examples()
    show_configuration_tips()
    show_output_info()
    show_compliance_notes()
    show_troubleshooting()
    
    create_demo_config()
    
    print("🚀 Happy scraping!")
    print("=" * 60)

if __name__ == "__main__":
    main()

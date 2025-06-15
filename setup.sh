#!/bin/bash

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "Installing Playwright browsers..."
playwright install

echo ""
echo "Setup complete! You can now run the scraper with:"
echo "python pc_jewellers_scraper.py"
echo ""
echo "Or test selectors first with:"
echo "python selector_tester.py"

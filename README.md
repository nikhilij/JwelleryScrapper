# PC Jeweller Web Scraper

## 📦 Project Summary
This project provides a robust, scalable, and production-ready solution for scraping product data and images from the PC Jeweller website. It is designed to extract detailed information from:
- [All Jewellery](https://www.pcjeweller.com/all-jewellery.html)
- [Ready to Ship](https://www.pcjeweller.com/ready-to-ship.html)
- Any additional category/product links provided in `pcjeweller_links.json`

The scraper is engineered to handle bot protection, organize data by category, and download all product images efficiently.

---

## 🚀 Key Features
- **Category-wise Scraping:** Supports all major jewellery categories (Rings, Earrings, Pendants, Chains, Bracelets, etc.)
- **Comprehensive Data Extraction:** Fetches product name, price, weight, metal, stone, product URL, and more
- **Image Download:** Downloads all product images, organized in folders by category
- **Bot Protection Bypass:** Utilizes `cloudscraper`, `requests`, and optionally `undetected-chromedriver` for advanced anti-bot circumvention
- **CSV Output:** Structured, clean CSV output for easy analysis
- **Manual Fallback:** Includes a browser console script for manual extraction if automation is blocked
- **Error Handling & Logging:** Robust error management and progress logging

---

## 🛠️ Technologies Used
- Python 3.8+
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [cloudscraper](https://github.com/VeNoMouS/cloudscraper)
- [requests](https://docs.python-requests.org/)
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) (optional)
- Standard Python libraries: `os`, `csv`, `json`, `logging`, etc.

---

## 📂 Project Structure
```
/workspaces/JwelleryScrapper/
├── jewellery_scraper.py           # Main scraping script
├── pcjeweller_links.json          # List of category/product links
├── requirements.txt               # Python dependencies
├── output/
│   └── products.csv               # Final scraped data
├── images/
│   ├── rings/
│   ├── earrings/
│   ├── pendants/
│   └── ...
├── manual_extraction_guide.sh     # Manual scraping instructions
└── README.md
```

---

## ⚙️ Setup Instructions
1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd JwelleryScrapper
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **(Optional) Update `pcjeweller_links.json`**
   - Add or modify category/product links as needed

---

## 🏃 Usage Guide
### 1. Scrape All Jewellery and Ready-to-Ship Pages
```bash
python jewellery_scraper.py
```

### 2. Scrape from Custom JSON Links
```bash
python jewellery_scraper.py --json pcjeweller_links.json
```

### 3. Output
- **CSV:** All product data in `output/products.csv`
- **Images:** Downloaded to `images/<category>/`

---

## 🧠 How It Works
- The scraper loads category/product links from the main pages and/or `pcjeweller_links.json`.
- For each category, it fetches up to 150 products, extracting all available details.
- Product images are downloaded and saved in folders named after their category.
- All data is compiled into a single CSV file for analysis.
- If bot protection blocks automation, a manual browser script is provided as fallback.

---

## 📑 Data Schema (CSV Fields)
- `Product Name`
- `Category`
- `Price`
- `Weight`
- `Metal`
- `Stone`
- `Product URL`
- `Image Filenames`

**Sample Row:**
| Product Name | Category | Price | Weight | Metal | Stone | Product URL | Image Filenames |
|--------------|----------|-------|--------|-------|-------|-------------|-----------------|
| Elegant Gold Ring | Rings | ₹12,000 | 2.5g | 18K Gold | Diamond | https://... | img1.jpg;img2.jpg |

---

## 🛡️ Troubleshooting & Best Practices
- If you encounter blocks, try running with a VPN or different network.
- Use the manual extraction guide if all automated methods fail.
- Respect the website's terms of service and robots.txt.
- Avoid aggressive scraping (rate limit requests).

---

## ⚖️ Legal & Ethical Notice
This project is for educational and research purposes only. Always ensure you have permission to scrape a website and comply with its terms of service and legal requirements.

---

## 🙋 Contact & Credits
Developed by [Your Name/Team].
- For issues or contributions, please open an issue or pull request.
- Built with Python, BeautifulSoup, cloudscraper, and undetected-chromedriver.

---

**Happy Scraping!**

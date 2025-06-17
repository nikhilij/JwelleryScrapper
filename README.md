# PC Jeweller Web Scraper 🚲💹

## 📆 Project Summary

This project provides a robust, scalable, and production-ready solution for scraping product data and images from the [PC Jeweller](https://www.pcjeweller.com) website. It's engineered to extract detailed information from:

* **All Jewellery**
* **Ready to Ship**
* Any additional category/product links listed in `pcjeweller_links.json`

The scraper bypasses bot protections, organizes images by category, and outputs clean, structured data in CSV format.

---

## 🚀 Key Features

* **Category-wise Scraping**: Supports Rings, Earrings, Pendants, Chains, Bracelets, and more
* **Comprehensive Data Extraction**: Collects product name, price, weight, metal, stone, product URL, etc.
* **Image Download**: Downloads and organizes product images by category
* **Bot Protection Bypass**: Uses `cloudscraper`, `requests`, and optionally `undetected-chromedriver`
* **CSV Output**: Clean and structured CSV output
* **Manual Fallback**: Console-based extraction script included
* **Error Handling & Logging**: Logs progress and handles failures gracefully

---

## 🛠️ Technologies Used

* Python 3.8+
* BeautifulSoup
* cloudscraper
* requests
* undetected-chromedriver (optional)
* Standard Python libraries: `os`, `csv`, `json`, `logging`, etc.

---

## 📂 Project Structure

```
/JwelleryScrapper/
├── jewellery_scraper.py           # Main scraping script
├── pcjeweller_links.json          # Input links file
├── requirements.txt               # Project dependencies
├── output/
│   └── products.csv               # Final scraped dataset
├── images/
│   ├── rings/
│   ├── earrings/
│   └── ...
├── manual_extraction_guide.sh     # Script for manual scraping
└── README.md
```

---

## ⚙️ Setup Instructions

1. Clone the repository

```bash
git clone <repo-url>
cd JwelleryScrapper
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. (Optional) Edit `pcjeweller_links.json` with custom category/product links

---

## 🏃 Usage Guide

**1. Scrape All Default Categories**

```bash
python jewellery_scraper.py
```

**2. Scrape Using Custom JSON Links**

```bash
python jewellery_scraper.py --json pcjeweller_links.json
```

**3. Outputs**

* `output/products.csv` → Product Data
* `images/<category>/` → Product Images

---

## 🧠 How It Works

* Loads category/product URLs
* Extracts up to 150 products per category
* Fetches details and downloads images
* Compiles data to CSV
* Falls back to manual mode if blocked

---

## 📁 Data Schema (CSV Fields)

| Field        | Example           |
| ------------ | ----------------- |
| Product Name | Elegant Gold Ring |
| Category     | Rings             |
| Price        | ₹12,000           |
| Weight       | 2.5g              |
| Metal        | 18K Gold          |
| Stone        | Diamond           |
| Product URL  | https\://...      |
| Image Files  | img1.jpg;img2.jpg |

---

## 🛡️ Troubleshooting & Best Practices

* Use VPN or alternate networks if blocked
* Manual script available for fallback
* Respect robots.txt and terms of service
* Avoid frequent/repetitive requests

---

## ⚖️ Legal & Ethical Notice

> This tool is for educational and research purposes only. Ensure permission before scraping any site and comply with legal terms.

---

## 🤝🏼 Author & Contact

**Developed by [Nikhil Soni](https://github.com/nikhilij)**
Final Year CSE @ KIIT | Backend Developer | AI & Automation Enthusiast

Feel free to open issues or pull requests for contributions.
Built using Python, BeautifulSoup, cloudscraper, and a love for automation.

---

🌟 Star the repo if you find it helpful!
📬 [Connect on LinkedIn](https://www.linkedin.com/in/nikhilij/)

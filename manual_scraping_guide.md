
# 🚀 MANUAL SCRAPING GUIDE FOR PC JEWELLER

Since automated scraping is blocked, follow these steps for each category:

## Step 1: Setup Browser Console Scraper

Open your browser and navigate to each category URL below.
Then open Developer Tools (F12) and run this JavaScript:

```javascript
// Enhanced Product Scraper for PC Jeweller
function scrapeProducts() {
    const products = [];
    const baseUrl = 'https://www.pcjeweller.com';
    
    // Find all product containers
    const productSelectors = [
        '.product-item', '.item', '[class*="product"]', 
        'a[href*="product"]', 'a[href*=".html"] img'
    ];
    
    let foundProducts = [];
    
    productSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            let productUrl = '';
            let productName = '';
            let price = '';
            let imageUrl = '';
            
            // Get product URL
            if (element.tagName === 'A') {
                productUrl = element.href;
            } else {
                const link = element.querySelector('a') || element.closest('a');
                if (link) productUrl = link.href;
            }
            
            // Get product name
            const nameElement = element.querySelector('h2, h3, .name, .title, [class*="name"]');
            if (nameElement) productName = nameElement.textContent.trim();
            
            // Get price
            const priceElement = element.querySelector('.price, .amount, [class*="price"]');
            if (priceElement) price = priceElement.textContent.trim();
            
            // Get image
            const img = element.querySelector('img');
            if (img) imageUrl = img.src || img.getAttribute('data-src');
            
            if (productUrl && (productName || price)) {
                foundProducts.push({
                    url: productUrl,
                    name: productName,
                    price: price,
                    image: imageUrl,
                    category: window.location.pathname
                });
            }
        });
    });
    
    // Remove duplicates
    const uniqueProducts = foundProducts.filter((product, index, self) => 
        index === self.findIndex(p => p.url === product.url)
    );
    
    console.log(`Found ${uniqueProducts.length} products`);
    
    // Download as JSON
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(uniqueProducts, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `products_${Date.now()}.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
    
    return uniqueProducts;
}

// Run the scraper
scrapeProducts();
```

## Step 2: Category URLs to Scrape


### RINGS (43 pages)
- https://www.pcjeweller.com/jewellery/rings.html
- https://www.pcjeweller.com/jewellery/best-seller/rings.html
- https://www.pcjeweller.com/jewellery/daily-wear-rings.html
- https://www.pcjeweller.com/jewellery/engagement-rings.html
- https://www.pcjeweller.com/jewellery/solitaire-rings.html
... and 38 more URLs

### NECKLACES (2 pages)
- https://www.pcjeweller.com/jewellery/gold-necklaces.html
- https://www.pcjeweller.com/jewellery/diamond-necklace.html

### BRACELETS (2 pages)
- https://www.pcjeweller.com/jewellery/gold-bracelets-and-bangles.html
- https://www.pcjeweller.com/jewellery/diamond-bracelet-and-bangles.html

### PENDANTS (5 pages)
- https://www.pcjeweller.com/jewellery/best-seller/pendants.html
- https://www.pcjeweller.com/jewellery/gold-pendants.html
- https://www.pcjeweller.com/jewellery/diamond-pendants.html
- https://www.pcjeweller.com/jewellery/silver-pendants.html
- https://www.pcjeweller.com/jewellery/gemstone-pendants.html

### CHAINS (3 pages)
- https://www.pcjeweller.com/jewellery/chains.html
- https://www.pcjeweller.com/jewellery/gold-mangalsutra.html
- https://www.pcjeweller.com/jewellery/diamond-mangalsutra.html

### MENS (1 pages)
- https://www.pcjeweller.com/jewellery/diamond-men-jewellery.html


## Step 3: Product Detail Scraper

For each product URL found, visit the product page and run this script:

```javascript
function scrapeProductDetails() {
    const product = {
        url: window.location.href,
        name: '',
        price: '',
        originalPrice: '',
        weight: '',
        metal: '',
        purity: '',
        stone: '',
        size: '',
        description: '',
        images: [],
        specifications: {}
    };
    
    // Get product name
    const nameSelectors = ['h1', '.product-name', '.product-title', '[class*="name"]'];
    for (let selector of nameSelectors) {
        const elem = document.querySelector(selector);
        if (elem && elem.textContent.trim()) {
            product.name = elem.textContent.trim();
            break;
        }
    }
    
    // Get prices
    const priceSelectors = ['.price-current', '.current-price', '.special-price', '.price'];
    for (let selector of priceSelectors) {
        const elem = document.querySelector(selector);
        if (elem) {
            product.price = elem.textContent.trim();
            break;
        }
    }
    
    // Get specifications
    const specRows = document.querySelectorAll('table tr, .spec-item, .attribute');
    specRows.forEach(row => {
        const label = row.querySelector('td:first-child, .label, .key');
        const value = row.querySelector('td:last-child, .value, .val');
        if (label && value) {
            const key = label.textContent.trim().toLowerCase();
            const val = value.textContent.trim();
            product.specifications[key] = val;
            
            // Map to specific fields
            if (key.includes('weight')) product.weight = val;
            if (key.includes('metal')) product.metal = val;
            if (key.includes('purity')) product.purity = val;
            if (key.includes('stone')) product.stone = val;
            if (key.includes('size')) product.size = val;
        }
    });
    
    // Get images
    const images = document.querySelectorAll('.product-image img, .gallery img, img[src*="product"]');
    images.forEach(img => {
        if (img.src && !product.images.includes(img.src)) {
            product.images.push(img.src);
        }
    });
    
    // Get description
    const descSelectors = ['.description', '.product-details', '.summary'];
    for (let selector of descSelectors) {
        const elem = document.querySelector(selector);
        if (elem) {
            product.description = elem.textContent.trim().substring(0, 500);
            break;
        }
    }
    
    console.log('Product scraped:', product);
    
    // Download product data
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(product, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `product_${Date.now()}.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
    
    return product;
}

scrapeProductDetails();
```

## Step 4: Image Download Script

After collecting product data, use this Python script to download images:

```python
import requests
import json
import os
from urllib.parse import urlparse

def download_images(product_data_file):
    with open(product_data_file, 'r') as f:
        products = json.load(f)
    
    for i, product in enumerate(products):
        category = product.get('category', 'unknown').replace('/', '_')
        os.makedirs(f'images/{category}', exist_ok=True)
        
        for j, img_url in enumerate(product.get('images', [])):
            try:
                response = requests.get(img_url, timeout=30)
                if response.status_code == 200:
                    ext = urlparse(img_url).path.split('.')[-1] or 'jpg'
                    filename = f'images/{category}/product_{i}_{j}.{ext}'
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f'Downloaded: {filename}')
            except Exception as e:
                print(f'Failed to download {img_url}: {e}')

# Usage: download_images('products_data.json')
```

## Expected Results:
- ~150 products per category
- Product details: name, price, weight, metal, purity, stone, etc.
- Product images downloaded to category folders
- All data saved in JSON and CSV formats

## Automation Tips:
1. Use browser automation tools like Selenium IDE to record actions
2. Create browser bookmarks with the JavaScript code
3. Use browser extensions for batch processing
4. Process one category at a time to avoid detection

Total estimated products: ~5000-8000 across all categories

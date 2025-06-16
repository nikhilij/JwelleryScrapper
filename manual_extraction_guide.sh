#!/bin/bash

# PC Jeweller Scraper - Manual Browser Method
# Since automated scraping is blocked, this script provides instructions
# for manual link extraction using browser developer tools

echo "=================================================="
echo "PC Jeweller Link Extraction - Manual Method"
echo "=================================================="
echo ""
echo "Since automated scraping is blocked by bot protection,"
echo "please follow these steps to extract links manually:"
echo ""
echo "1. Open your web browser and navigate to:"
echo "   https://www.pcjeweller.com/all-jewellery.html"
echo ""
echo "2. Open Developer Tools (Press F12 or Ctrl+Shift+I)"
echo ""
echo "3. Go to the Console tab"
echo ""
echo "4. Copy and paste the following JavaScript code:"
echo ""
echo "----------------------------------------"
cat << 'EOF'
// Extract all links from the page
var links = [];
var uniqueUrls = new Set();

document.querySelectorAll('a[href]').forEach(function(link) {
    var url = link.href;
    var text = link.textContent.trim();
    
    // Skip duplicates and unwanted links
    if (!uniqueUrls.has(url) && url !== window.location.href && 
        !url.includes('javascript:') && !url.includes('mailto:')) {
        
        uniqueUrls.add(url);
        links.push({
            url: url,
            text: text,
            title: link.title || '',
            className: link.className || ''
        });
    }
});

console.log('Found ' + links.length + ' unique links');

// Display first 5 links as preview
console.log('\nFirst 5 links:');
links.slice(0, 5).forEach(function(link, index) {
    console.log((index + 1) + '. ' + link.url);
    if (link.text) console.log('   Text: ' + link.text);
});

// Create download link for JSON file
var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(links, null, 2));
var downloadAnchorNode = document.createElement('a');
downloadAnchorNode.setAttribute("href", dataStr);
downloadAnchorNode.setAttribute("download", "pcjeweller_links.json");
downloadAnchorNode.style.display = 'none';
document.body.appendChild(downloadAnchorNode);
downloadAnchorNode.click();
downloadAnchorNode.remove();

console.log('\nLinks exported to pcjeweller_links.json');
console.log('Check your Downloads folder for the file.');
EOF
echo "----------------------------------------"
echo ""
echo "5. Press Enter to execute the code"
echo ""
echo "6. The script will:"
echo "   - Extract all unique links from the page"
echo "   - Show a preview in the console"
echo "   - Download a JSON file with all links to your Downloads folder"
echo ""
echo "7. The downloaded file will contain all extracted links with:"
echo "   - URL"
echo "   - Link text"
echo "   - Title attribute"
echo "   - CSS classes"
echo ""
echo "Alternative: Extract as CSV"
echo "============================"
echo ""
echo "If you prefer CSV format, use this code instead:"
echo ""
cat << 'EOF'
// Extract links as CSV
var csvContent = "URL,Text,Title,ClassName\n";
var uniqueUrls = new Set();

document.querySelectorAll('a[href]').forEach(function(link) {
    var url = link.href;
    var text = link.textContent.trim().replace(/"/g, '""');
    var title = (link.title || '').replace(/"/g, '""');
    var className = (link.className || '').replace(/"/g, '""');
    
    if (!uniqueUrls.has(url) && url !== window.location.href && 
        !url.includes('javascript:') && !url.includes('mailto:')) {
        
        uniqueUrls.add(url);
        csvContent += '"' + url + '","' + text + '","' + title + '","' + className + '"\n';
    }
});

// Download CSV
var dataStr = "data:text/csv;charset=utf-8," + encodeURIComponent(csvContent);
var downloadAnchorNode = document.createElement('a');
downloadAnchorNode.setAttribute("href", dataStr);
downloadAnchorNode.setAttribute("download", "pcjeweller_links.csv");
downloadAnchorNode.style.display = 'none';
document.body.appendChild(downloadAnchorNode);
downloadAnchorNode.click();
downloadAnchorNode.remove();

console.log('Links exported to pcjeweller_links.csv');
EOF
echo ""
echo "This method will successfully bypass the bot protection"
echo "since it runs in your actual browser session."
echo ""
echo "=================================================="

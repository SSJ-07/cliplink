# Real Product Search Implementation

## Overview

ClipLink now searches **real products from actual e-commerce websites** instead of a static database!

## How It Works

```
1. Extract frames from Instagram Reel
2. Analyze with Google Vision API:
   - Labels (e.g., "shoe", "denim", "clothing")
   - Logos (e.g., Nike swoosh, Adidas logo)
   - Text (e.g., "ZARA", "H&M" text in image)
3. Detect brand from logos/text
4. Build search query (labels + user description + brand)
5. Route search based on brand:
   - If Nike detected → Search Nike.com
   - If Zara detected → Search Zara.com
   - Otherwise → Google Shopping → Amazon fallback
6. Return real products with current prices
```

## Supported Brands

The system recognizes 15+ major brands:

### Fashion
- Nike
- Adidas  
- Zara
- H&M
- Uniqlo
- Levi's
- Gap

### Tech
- Apple
- Samsung

### Retail
- Target
- Walmart
- IKEA

### Beauty
- Sephora

## Search Strategy

### 1. Brand-Aware Search (Best)

When a brand is detected:
```python
# Example: Nike logo detected + "white shoes" description
→ Search: "Nike white shoes"
→ Route to: Nike.com search page
```

### 2. Google Shopping (Primary)

Uses SerpAPI for Google Shopping results:
```python
→ Search: "white running shoes"
→ Returns: Top 5 products from Google Shopping
→ Includes: prices, images, direct links
```

### 3. Amazon Fallback

If Google Shopping fails or no API key:
```python
→ Search Amazon.com
→ Scrape product results
→ Return product cards
```

## Setup

### 1. Get SerpAPI Key (Recommended)

1. Go to https://serpapi.com/
2. Sign up (free tier: 100 searches/month)
3. Get API key from dashboard
4. Add to `.env`:
```bash
SERPAPI_KEY=your-key-here
```

**Without SerpAPI**: System falls back to Amazon search (works but less accurate)

### 2. Dependencies

Already installed:
```bash
pip install beautifulsoup4  # Web scraping
pip install lxml            # HTML parsing
pip install google-search-results  # SerpAPI client
```

### 3. Test It

```bash
# Test with text query (no video)
curl -X POST http://localhost:5001/api/search-products \
  -H "Content-Type: application/json" \
  -d '{"query":"nike air max 270"}'

# Expected response:
{
  "products": [
    {
      "title": "Nike Air Max 270",
      "price": 150.00,
      "image_url": "https://...",
      "product_url": "https://...",
      "source": "Google Shopping"
    }
  ]
}
```

## Example Results

### Nike Shoes Detected
```json
{
  "detected_brand": "nike",
  "detected_labels": [
    {"label": "Footwear", "confidence": 0.95},
    {"label": "Shoe", "confidence": 0.93}
  ],
  "products": [
    {
      "title": "Nike Air Max 270 Running Shoes",
      "price": 150.00,
      "source": "Google Shopping",
      "product_url": "https://nike.com/..."
    }
  ]
}
```

### Zara Clothing Detected
```json
{
  "detected_brand": "zara",
  "detected_labels": [
    {"label": "Clothing", "confidence": 0.92},
    {"label": "Top", "confidence": 0.88}
  ],
  "products": [
    {
      "title": "Search results for '...' on Zara",
      "source": "Zara",
      "product_url": "https://www.zara.com/search?q=..."
    }
  ]
}
```

## API Features

### Logo Detection

Google Vision API detects brand logos:
```python
logos = vision_service.get_logos(frame)
# Returns: [{"description": "Nike", "score": 0.95}]
```

### Text Detection  

Extracts brand names from text in images:
```python
texts = vision_service.get_text(frame)
# Returns: ["ZARA", "100% Cotton", "Size M"]
```

### Brand Recognition

Smart brand matching:
```python
brand = web_search_service.detect_brand(logos, texts, labels)
# Checks: logos → text → labels
# Returns: "nike" or "zara" or None
```

## Cost Per Request

With SerpAPI:
- Google Vision: $0.0045 (3 frames)
- SerpAPI: Free (100/month) or $0.005 (paid)
- **Total**: ~$0.005 per search

Without SerpAPI (free):
- Google Vision: $0.0045
- Amazon scraping: Free
- **Total**: ~$0.0045 per search

## Limitations

### 1. Brand Website Scraping

Most brand websites (Nike, Zara, etc.) have anti-scraping protection. Currently returns search page links instead of specific products.

**Solution**: Use their official APIs if available (requires partnerships)

### 2. Rate Limits

- SerpAPI free tier: 100 searches/month
- Google Vision: 1000 images/month free
- Amazon: No official limit but can block

**Solution**: Implement caching for popular queries

### 3. Price Accuracy

Prices from Google Shopping may not be real-time current.

**Solution**: Prices are clickable links to actual product pages

## Future Improvements

### 1. Use Brand APIs

```python
# Nike: Nike API (requires partnership)
# Amazon: Product Advertising API (requires approval)
# Shopify: Storefront API (for Shopify stores)
```

### 2. Add More Sources

```python
# eBay, Etsy, AliExpress, Walmart, etc.
```

### 3. Image-Based Search

```python
# Google Lens API
# Pinterest Visual Search
# TinEye for product matching
```

### 4. Caching Layer

```python
# Redis cache for popular queries
# Store search results for 24 hours
```

## Troubleshooting

### No products found

**Check**:
1. Is SERPAPI_KEY set? (if not, uses Amazon fallback)
2. Is internet connection working?
3. Check logs for API errors

### Brand not detected

**Check**:
1. Is logo clearly visible in reel?
2. Is brand in supported list?
3. Try adding brand name in description

### Products not loading

**Check**:
1. Product URLs are valid
2. Images load (some may have CORS issues)
3. Frontend console for errors

## Testing

```bash
# Test brand detection
curl -X POST http://localhost:5001/api/analyze-reel \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://instagram.com/reel/nike-shoes/",
    "note": "white running shoes"
  }'

# Test text search
curl -X POST http://localhost:5001/api/search-products \
  -H "Content-Type: application/json" \
  -d '{"query":"blue adidas shoes"}'
```

## Production Recommendations

1. **Get SerpAPI Key** - Much better results than scraping
2. **Implement Caching** - Save API calls and money
3. **Add Analytics** - Track which brands/products are popular
4. **Monitor Costs** - Set up billing alerts
5. **Rate Limiting** - Prevent abuse

## Support

Questions? Check:
- [Main README](../README.md)
- [Setup Guide](../SETUP_GUIDE.md)
- Backend logs for detailed errors


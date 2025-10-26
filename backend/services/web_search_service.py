"""
Web Search Service - Real-time product search from e-commerce sites
Supports brand-aware routing to official websites + Google Custom Search fallback

NOTE: Replaced SerpAPI with Google Custom Search JSON API.
Set GOOGLE_API_KEY and GOOGLE_CX_ID in backend/.env
Docs: https://developers.google.com/custom-search/v1/overview
"""
import os
import logging
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
# SerpAPI removed in favor of Google Custom Search JSON API

logger = logging.getLogger(__name__)


class WebSearchService:
    """Service for searching real products from e-commerce websites"""
    
    # Brand website search URLs
    BRAND_SITES = {
        "nike": {
            "url": "https://www.nike.com/w?q={query}",
            "name": "Nike"
        },
        "adidas": {
            "url": "https://www.adidas.com/us/search?q={query}",
            "name": "Adidas"
        },
        "zara": {
            "url": "https://www.zara.com/us/en/search?searchTerm={query}",
            "name": "Zara"
        },
        "h&m": {
            "url": "https://www2.hm.com/en_us/search-results.html?q={query}",
            "name": "H&M"
        },
        "hm": {
            "url": "https://www2.hm.com/en_us/search-results.html?q={query}",
            "name": "H&M"
        },
        "uniqlo": {
            "url": "https://www.uniqlo.com/us/en/search/?q={query}",
            "name": "Uniqlo"
        },
        "levi's": {
            "url": "https://www.levi.com/US/en_US/search?q={query}",
            "name": "Levi's"
        },
        "levis": {
            "url": "https://www.levi.com/US/en_US/search?q={query}",
            "name": "Levi's"
        },
        "gap": {
            "url": "https://www.gap.com/browse/search.do?searchText={query}",
            "name": "Gap"
        },
        "apple": {
            "url": "https://www.apple.com/shop/search/{query}",
            "name": "Apple"
        },
        "samsung": {
            "url": "https://www.samsung.com/us/search/?searchvalue={query}",
            "name": "Samsung"
        },
        "sephora": {
            "url": "https://www.sephora.com/search?keyword={query}",
            "name": "Sephora"
        },
        "ikea": {
            "url": "https://www.ikea.com/us/en/search/?q={query}",
            "name": "IKEA"
        },
        "target": {
            "url": "https://www.target.com/s?searchTerm={query}",
            "name": "Target"
        },
        "walmart": {
            "url": "https://www.walmart.com/search?q={query}",
            "name": "Walmart"
        }
    }
    
    def __init__(self):
        """Initialize web search service"""
        # Google Custom Search JSON API
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx_id = os.getenv("GOOGLE_CX_ID")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    def detect_brand(self, logos: List[Dict], texts: List[str], labels: List[Dict]) -> Optional[str]:
        """
        Detect brand from logos, text, and labels
        
        Args:
            logos: List of detected logos
            texts: List of text detected in image
            labels: List of image labels
            
        Returns:
            Brand name (lowercase) or None
        """
        # Check logos first (highest confidence)
        for logo in logos:
            brand = logo['description'].lower()
            if brand in self.BRAND_SITES:
                logger.info(f"Brand detected from logo: {brand}")
                return brand
        
        # Check text for brand names
        for text in texts:
            text_lower = text.lower()
            for brand in self.BRAND_SITES.keys():
                if brand in text_lower:
                    logger.info(f"Brand detected from text: {brand}")
                    return brand
        
        # Check web entities/labels as last resort
        for label in labels:
            label_lower = label['description'].lower()
            if label_lower in self.BRAND_SITES:
                logger.info(f"Brand detected from label: {label_lower}")
                return label_lower
        
        logger.info("No brand detected")
        return None
    
    def search_google_custom(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Backward-compatible: basic single-query search via Google Custom Search.
        Kept for compatibility; new flow uses minimal beam search.
        """
        if not self.google_api_key or not self.google_cx_id:
            logger.warning("GOOGLE_API_KEY/GOOGLE_CX_ID not set, skipping Google Custom Search")
            return []

        try:
            url = (
                "https://www.googleapis.com/customsearch/v1"
                f"?q={requests.utils.quote(query)}&key={self.google_api_key}&cx={self.google_cx_id}"
            )
            resp = requests.get(url, headers=self.headers, timeout=10)
            data = resp.json()

            items = data.get("items", [])
            out: List[Dict] = []
            for item in items[:num_results]:
                pagemap = item.get("pagemap", {})
                metatags = (pagemap.get("metatags") or [{}])[0]
                og_image = metatags.get("og:image") or metatags.get("twitter:image")
                cse_images = pagemap.get("cse_image")
                image_url = ""
                if og_image:
                    image_url = og_image
                elif isinstance(cse_images, list) and cse_images and isinstance(cse_images[0], dict):
                    image_url = cse_images[0].get("src", "")

                out.append({
                    "id": "",
                    "title": item.get("title", ""),
                    "description": item.get("snippet", ""),
                    "price": 0.0,
                    "currency": "USD",
                    "image_url": image_url,
                    "product_url": item.get("link", ""),
                    "source": item.get("displayLink", "Google"),
                    "tags": []
                })

            logger.info(f"Found {len(out)} products from Google Custom Search (single query)")
            return out
        except Exception as e:
            logger.error(f"Error searching Google Custom: {e}")
            return []

    # -------- New minimal beam search with URL scoring --------
    BAD_FRAGMENTS = [
        "/search", "/category", "/collections", "/collection", "/w/", "/c/", "/brand",
        "/men/", "/women/", "/kids/", "/golf", "/stories", "/help", "/news", "/blog",
        "/sale", "/home", "/store", "/stores", "/sneakers/", "/shop/", "/collections/"
    ]
    PRODUCT_HINTS = [
        "/t/", "/product/", "/p/", "/dp/", "/gp/product/", "/item/"
    ]
    
    def is_pdp(self, url: str) -> bool:
        """Check if URL is likely a product detail page"""
        if not url:
            return False
        u = url.lower()
        good = any(h in u for h in self.PRODUCT_HINTS)
        bad = any(f in u for f in self.BAD_FRAGMENTS)
        return good and not bad

    def _enhance_query_variants(self, raw_query: str, brand: Optional[str] = None,
                                color: Optional[str] = None, item: Optional[str] = None) -> List[str]:
        q_base = (raw_query or "").strip()
        variants: List[str] = [q_base]
        slots = " ".join([x for x in [brand, color, item] if x])
        if slots:
            variants.append(slots)
        if q_base:
            variants.append(f"{q_base} product")
        if brand and item:
            variants.append(f"{brand} {item}")
        # de-duplicate, preserve order
        seen = set()
        deduped: List[str] = []
        for v in variants:
            v = " ".join(v.split())
            low = v.lower()
            if low and low not in seen:
                seen.add(low)
                deduped.append(v)
        logger.info(f"[search] variants = {deduped}")
        return deduped

    def _google_custom_raw(self, query: str, start: int = 1, num: int = 10) -> List[Dict]:
        if not self.google_api_key or not self.google_cx_id:
            return []
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {"key": self.google_api_key, "cx": self.google_cx_id, "q": query, "num": num, "start": start}
            data = requests.get(url, params=params, headers=self.headers, timeout=8).json()
            items = data.get("items", []) or []
            results: List[Dict] = []
            for it in items:
                r = {
                    "title": it.get("title"),
                    "url": it.get("link"),
                    "snippet": it.get("snippet"),
                    "domain": it.get("displayLink"),
                    "pagemap": it.get("pagemap", {})
                }
                meta = (r["pagemap"].get("metatags") or [{}])[0]
                if "og:image" in meta:
                    r["image"] = meta["og:image"]
                results.append(r)
            return results
        except Exception:
            return []

    def _score_url(self, url: str, title: Optional[str] = None) -> float:
        u = (url or "").lower()
        score = 0.0
        if any(f in u for f in self.BAD_FRAGMENTS):
            score -= 2.0
        if any(h in u for h in self.PRODUCT_HINTS):
            score += 2.5
        if u.startswith("https://"):
            score += 0.3
        if u.count("/") >= 4:
            score += 0.5
        t = (title or "").lower()
        if "logo" in t or "home" in t:
            score -= 1.0
        if any(k in t for k in ["product", "shoe", "sneaker", "jacket", "bag", "dress", "top", "pants"]):
            score += 0.4
        return score

    def _filter_and_rank(self, raw_results: List[Dict]) -> List[Dict]:
        scored: List[Dict] = []
        for r in raw_results:
            url = r.get("url")
            if not url:
                continue
            s = self._score_url(url, r.get("title"))
            r["_url_score"] = s
            scored.append(r)
        kept = [r for r in scored if r["_url_score"] > -1.0]
        kept.sort(key=lambda x: x["_url_score"], reverse=True)
        return kept

    def _search_products_minimal_beam(self, raw_query: str, brand: Optional[str] = None,
                                       color: Optional[str] = None, item: Optional[str] = None,
                                       pages: int = 2) -> List[Dict]:
        queries = self._enhance_query_variants(raw_query, brand, color, item)
        aggregated: List[Dict] = []
        for q in queries:
            for p in range(pages):
                start = 1 + p * 10
                results = self._google_custom_raw(q, start=start, num=10)
                aggregated.extend(results)
        logger.info(f"[search] top urls (pre-filter) = {[r.get('url') for r in aggregated[:10]]}")
        ranked = self._filter_and_rank(aggregated)
        logger.info(f"[search] top urls (ranked) = {[r.get('url') for r in ranked[:10]]}")
        # de-dup by URL
        seen = set()
        deduped: List[Dict] = []
        for r in ranked:
            u = r.get("url")
            if not u:
                continue
            if u not in seen:
                seen.add(u)
                deduped.append(r)
        return deduped[:20]
    
    def search_amazon(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Search Amazon products
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of product dicts
        """
        try:
            url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            products = []
            items = soup.select('[data-component-type="s-search-result"]')[:num_results]
            
            for item in items:
                try:
                    title_elem = item.select_one('h2 a span')
                    link_elem = item.select_one('h2 a')
                    price_elem = item.select_one('.a-price .a-offscreen')
                    image_elem = item.select_one('img.s-image')
                    
                    if title_elem and link_elem:
                        product_url = link_elem.get('href', '')
                        if product_url and not product_url.startswith('http'):
                            product_url = f"https://www.amazon.com{product_url}"
                        
                        products.append({
                            "id": "",
                            "title": title_elem.text.strip(),
                            "description": title_elem.text.strip()[:200],
                            "price": self._parse_price(price_elem.text if price_elem else ""),
                            "currency": "USD",
                            "image_url": image_elem.get('src', '') if image_elem else "",
                            "product_url": product_url,
                            "source": "Amazon",
                            "tags": []
                        })
                except Exception as e:
                    logger.error(f"Error parsing Amazon item: {e}")
                    continue
            
            logger.info(f"Found {len(products)} products from Amazon")
            return products
            
        except Exception as e:
            logger.error(f"Error searching Amazon: {e}")
            return []
    
    def search_brand_website(self, brand: str, query: str, num_results: int = 3) -> List[Dict]:
        """
        Search a specific brand's website
        
        Args:
            brand: Brand name (lowercase)
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of product dicts
        """
        brand = brand.lower()
        
        if brand not in self.BRAND_SITES:
            logger.warning(f"Brand {brand} not in supported sites")
            return []
        
        try:
            brand_info = self.BRAND_SITES[brand]
            url = brand_info["url"].format(query=query.replace(' ', '+'))
            brand_name = brand_info["name"]
            
            logger.info(f"Searching {brand_name} website: {url}")
            
            # Return branded search link (actual scraping would violate ToS for most sites)
            # Instead, return a generic result pointing to the search page
            return [{
                "id": f"{brand}-search",
                "title": f"Search results for '{query}' on {brand_name}",
                "description": f"Click to view {query} products on {brand_name} official website",
                "price": 0,
                "currency": "USD",
                "image_url": "",
                "product_url": url,
                "source": brand_name,
                "tags": [brand]
            }]
            
        except Exception as e:
            logger.error(f"Error searching {brand} website: {e}")
            return []
    
    def search_products(
        self,
        query: str,
        brand: Optional[str] = None,
        num_results: int = 5
    ) -> List[Dict]:
        """
        Search for products with brand-aware routing
        
        Args:
            query: Search query
            brand: Detected brand (optional)
            num_results: Number of results to return
            
        Returns:
            List of product dicts
        """
        products = []
        
        # Strategy 1: If brand detected, search brand website first
        if brand and brand.lower() in self.BRAND_SITES:
            logger.info(f"Using brand-aware search for: {brand}")
            brand_products = self.search_brand_website(brand, query, num_results=1)
            products.extend(brand_products)
        
        # Strategy 2: Minimal beam search to get better PDPs
        candidates: List[Dict] = []
        beam_results = self._search_products_minimal_beam(query, brand=brand)
        
        for item in beam_results:
            # Skip logo-like titles/urls
            title = (item.get("title") or "").lower()
            url = item.get("url") or ""
            if "logo" in title or "/logo" in url.lower():
                continue
            
            # Only keep PDPs
            if not self.is_pdp(url):
                continue

            pagemap = item.get("pagemap", {})
            meta = (pagemap.get("metatags") or [{}])[0]
            og_image = meta.get("og:image") or meta.get("twitter:image")
            cse_images = pagemap.get("cse_image")
            image_url = ""
            if og_image:
                image_url = og_image
            elif isinstance(cse_images, list) and cse_images and isinstance(cse_images[0], dict):
                image_url = cse_images[0].get("src", "")

            candidates.append({
                "id": "",
                "title": item.get("title", ""),
                "description": item.get("snippet", ""),
                "price": 0.0,
                "currency": "USD",
                "image_url": image_url,
                "product_url": url,
                "source": item.get("domain", "Google"),
                "tags": []
            })

        # If no PDPs found, try to extract from category pages
        if not candidates and beam_results:
            logger.info("No PDPs found, trying to extract from category pages...")
            for item in beam_results[:3]:  # Try first 3 results
                url = item.get("url", "")
                if url and not self.is_pdp(url):
                    extracted_links = self._extract_product_links(url)
                    for link in extracted_links[:2]:  # Max 2 per category
                        if self.is_pdp(link):
                            candidates.append({
                                "id": "",
                                "title": f"Extracted from {item.get('title', 'category')}",
                                "description": "Auto-extracted product link",
                                "price": 0.0,
                                "currency": "USD",
                                "image_url": "",
                                "product_url": link,
                                "source": item.get("domain", "Google"),
                                "tags": []
                            })

        # If still no candidates, fallback to basic single query
        if not candidates:
            logger.warning("No PDPs found, falling back to basic search")
            candidates = self.search_google_custom(query, num_results=num_results)

        products.extend(candidates[:max(0, num_results - len(products))])
        
        # Strategy 3: Fallback to Amazon if still need more results
        if len(products) < num_results:
            amazon_products = self.search_amazon(query, num_results=num_results-len(products))
            products.extend(amazon_products)
        
        # Add similarity score (all results are relevant)
        for i, product in enumerate(products):
            product['similarity_score'] = 1.0 - (i * 0.1)  # Decreasing score
        
        logger.info(f"Total products found: {len(products)}")
        return products[:num_results]

    def _extract_product_links(self, category_url: str) -> List[str]:
        """Extract likely product detail links from a category/search page."""
        try:
            if not category_url:
                return []
            html = requests.get(category_url, headers=self.headers, timeout=5).text
            soup = BeautifulSoup(html, "html.parser")
            links: List[str] = []
            candidates = ["/t/", "/product/", "/p/"]
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(x in href for x in candidates):
                    if not href.startswith("http"):
                        # Heuristic for same-host absolute URL
                        try:
                            base = category_url.split("/")[2]
                            href = f"https://{base}{href if href.startswith('/') else '/' + href}"
                        except Exception:
                            continue
                    links.append(href)
            # Deduplicate while preserving order
            seen = set()
            unique_links = []
            for l in links:
                if l not in seen:
                    seen.add(l)
                    unique_links.append(l)
            return unique_links[:10]
        except Exception as _:
            return []
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price string to float"""
        try:
            # Remove currency symbols and commas
            clean_price = price_str.replace('$', '').replace(',', '').strip()
            # Extract first number
            import re
            match = re.search(r'[\d.]+', clean_price)
            if match:
                return float(match.group())
        except Exception:
            pass
        return 0.0


# Singleton instance
_web_search_service = None

def get_web_search_service() -> WebSearchService:
    """Get or create WebSearchService singleton"""
    global _web_search_service
    if _web_search_service is None:
        _web_search_service = WebSearchService()
    return _web_search_service


"""
Frame Understanding Service
Extracts structured product information from video frames
"""
import logging
import re
from typing import List, Dict, Optional
from services.vision_service import VisionService

logger = logging.getLogger(__name__)


class FrameUnderstandingService:
    """Service for extracting structured product information from frames"""
    
    # Common product types from labels
    PRODUCT_TYPE_KEYWORDS = {
        'footwear': ['footwear', 'shoe', 'sneaker', 'boot', 'sandal', 'heel'],
        'clothing': ['clothing', 'apparel', 'shirt', 'jacket', 'dress', 'pants', 'jeans', 'top', 'bottom'],
        'accessory': ['accessory', 'bag', 'watch', 'jewelry', 'hat', 'belt', 'sunglasses'],
        'electronics': ['phone', 'laptop', 'tablet', 'headphones', 'earbuds', 'camera'],
        'beauty': ['cosmetics', 'makeup', 'perfume', 'skincare', 'lipstick'],
        'furniture': ['furniture', 'chair', 'table', 'sofa', 'bed', 'desk']
    }
    
    # Color keywords from labels
    COLOR_KEYWORDS = [
        'black', 'white', 'blue', 'red', 'green', 'yellow', 'orange', 'purple',
        'pink', 'brown', 'gray', 'grey', 'beige', 'navy', 'maroon', 'tan',
        'silver', 'gold', 'bronze', 'cream', 'ivory'
    ]
    
    # Attribute keywords from labels
    ATTRIBUTE_KEYWORDS = {
        'style': ['casual', 'formal', 'athletic', 'vintage', 'modern', 'classic'],
        'material': ['leather', 'cotton', 'denim', 'silk', 'wool', 'synthetic', 'canvas'],
        'fit': ['slim', 'regular', 'loose', 'tight', 'oversized'],
        'features': ['waterproof', 'breathable', 'insulated', 'lightweight', 'stretchy']
    }
    
    def __init__(self):
        """Initialize frame understanding service"""
        pass
    
    def understand_frame(
        self,
        frame_base64: str,
        vision_service: VisionService,
        user_text: str = ""
    ) -> Dict:
        """
        Extract structured product information from frame
        
        Args:
            frame_base64: Base64 encoded frame
            vision_service: Vision service for API calls
            user_text: User's description (optional, helps contextualize)
            
        Returns:
            Structured query pack with product info
        """
        logger.info("Understanding frame content...")
        
        # Get vision data
        labels = vision_service.get_image_labels(frame_base64, max_results=20)
        logos = vision_service.get_logos(frame_base64)
        texts = vision_service.get_text(frame_base64)
        
        # Extract structured information
        query_pack = {
            'product_type': self._extract_product_type(labels, user_text),
            'brand': self._extract_brand(logos, texts, labels),
            'model_guess': self._extract_model(texts, user_text),
            'colors': self._extract_colors(labels, user_text),
            'visible_text': texts,
            'attributes': self._extract_attributes(labels),
            'ocr_text': ' '.join(texts) if texts else '',
            'labels': [l['description'] for l in labels],
            'logos': [l['description'] for l in logos],
            'user_text': user_text
        }
        
        logger.info(f"Extracted query pack: {self._format_query_pack_summary(query_pack)}")
        return query_pack
    
    def _extract_product_type(self, labels: List[Dict], user_text: str) -> Optional[str]:
        """Extract product type from labels and user text"""
        label_descriptions = ' '.join([l['description'].lower() for l in labels])
        user_text_lower = user_text.lower()
        
        # Check user text first
        for product_type, keywords in self.PRODUCT_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in user_text_lower:
                    logger.info(f"Product type from user text: {product_type}")
                    return product_type
        
        # Check labels
        for product_type, keywords in self.PRODUCT_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in label_descriptions:
                    logger.info(f"Product type from labels: {product_type}")
                    return product_type
        
        # Default
        return None
    
    def _extract_brand(
        self,
        logos: List[Dict],
        texts: List[str],
        labels: List[Dict]
    ) -> Optional[str]:
        """Extract brand from logos, text, and labels"""
        # Check logos first (highest confidence)
        if logos:
            brand = logos[0]['description']
            logger.info(f"Brand from logo: {brand}")
            return brand
        
        # Check OCR text for brand names
        known_brands = [
            'nike', 'adidas', 'zara', 'h&m', 'uniqlo', 'levi', 'gap',
            'apple', 'samsung', 'sony', 'canon', 'gucci', 'prada',
            'north face', 'patagonia', 'columbia', 'vans', 'converse'
        ]
        
        for text in texts:
            text_lower = text.lower()
            for brand in known_brands:
                if brand in text_lower:
                    logger.info(f"Brand from OCR: {brand}")
                    return brand.title()
        
        # Check labels
        for label in labels:
            label_lower = label['description'].lower()
            for brand in known_brands:
                if brand == label_lower:
                    logger.info(f"Brand from label: {brand}")
                    return brand.title()
        
        return None
    
    def _extract_model(self, texts: List[str], user_text: str) -> Optional[str]:
        """Extract model name/number from OCR text and user description"""
        # Look for model patterns in OCR text
        model_patterns = [
            r'[A-Z]{2,}\s*\d{2,}',  # e.g., "AF1", "MAX 270"
            r'\b[A-Z][0-9]{3,}\b',  # e.g., "X1000"
            r'\b\d{3,}-\d{3,}\b'    # e.g., "123-456" (SKU)
        ]
        
        for text in texts:
            for pattern in model_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    model = matches[0]
                    logger.info(f"Model extracted from OCR: {model}")
                    return model
        
        # Check user text for model names (common ones)
        common_models = [
            'air force 1', 'air max', 'jordan', 'ultraboost', 'stan smith',
            'chuck taylor', 'old skool', 'classic', 'original'
        ]
        
        user_text_lower = user_text.lower()
        for model in common_models:
            if model in user_text_lower:
                logger.info(f"Model from user text: {model}")
                return model.title()
        
        return None
    
    def _extract_colors(self, labels: List[Dict], user_text: str) -> List[str]:
        """Extract colors from labels and user text"""
        colors = []
        
        # Check user text first
        user_text_lower = user_text.lower()
        for color in self.COLOR_KEYWORDS:
            if color in user_text_lower:
                colors.append(color)
        
        # Check labels
        label_descriptions = ' '.join([l['description'].lower() for l in labels])
        for color in self.COLOR_KEYWORDS:
            if color in label_descriptions and color not in colors:
                colors.append(color)
        
        if colors:
            logger.info(f"Colors extracted: {colors}")
        
        return colors[:3]  # Return top 3 colors
    
    def _extract_attributes(self, labels: List[Dict]) -> List[str]:
        """Extract product attributes from labels"""
        attributes = []
        label_descriptions = ' '.join([l['description'].lower() for l in labels])
        
        for category, keywords in self.ATTRIBUTE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in label_descriptions:
                    attributes.append(keyword)
        
        if attributes:
            logger.info(f"Attributes extracted: {attributes}")
        
        return list(set(attributes))[:5]  # Return top 5 unique attributes
    
    def _format_query_pack_summary(self, query_pack: Dict) -> str:
        """Format query pack for logging"""
        parts = []
        if query_pack.get('brand'):
            parts.append(f"brand={query_pack['brand']}")
        if query_pack.get('product_type'):
            parts.append(f"type={query_pack['product_type']}")
        if query_pack.get('model_guess'):
            parts.append(f"model={query_pack['model_guess']}")
        if query_pack.get('colors'):
            parts.append(f"colors={','.join(query_pack['colors'])}")
        return ', '.join(parts) if parts else 'generic product'


# Singleton instance
_frame_understanding_service = None

def get_frame_understanding_service() -> FrameUnderstandingService:
    """Get or create FrameUnderstandingService singleton"""
    global _frame_understanding_service
    if _frame_understanding_service is None:
        _frame_understanding_service = FrameUnderstandingService()
    return _frame_understanding_service

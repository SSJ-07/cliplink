"""
Google Vision API integration for image label detection
Based on visual-product-search-app architecture
"""
import os
import base64
import logging
from typing import List, Dict
from google.cloud import vision
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class VisionService:
    """Service for Google Cloud Vision API integration"""
    
    def __init__(self):
        """Initialize Vision API client with credentials"""
        # Support both credential file and base64 encoded credentials
        credentials = None
        
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            # Use credentials file path
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS_BASE64"):
            # Use base64 encoded credentials (for deployment)
            import json
            credentials_json = base64.b64decode(
                os.getenv("GOOGLE_APPLICATION_CREDENTIALS_BASE64")
            ).decode('utf-8')
            credentials_dict = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict
            )
        
        if credentials:
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
        else:
            # Try default credentials
            try:
                self.client = vision.ImageAnnotatorClient()
            except Exception as e:
                logger.warning(f"Could not initialize Vision API client: {e}")
                self.client = None
    
    def get_image_labels(self, image_base64: str, max_results: int = 10) -> List[Dict]:
        """
        Extract labels from image using Google Vision API
        
        Args:
            image_base64: Base64 encoded image
            max_results: Maximum number of labels to return
            
        Returns:
            List of label dicts with 'description' and 'score'
        """
        if not self.client:
            logger.warning("Vision API client not initialized")
            return []
        
        try:
            # Decode base64 image
            image_content = base64.b64decode(image_base64)
            
            # Create Vision API image object
            image = vision.Image(content=image_content)
            
            # Perform label detection
            response = self.client.label_detection(
                image=image,
                max_results=max_results
            )
            
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            # Filter labels with confidence > 0.5
            labels = []
            for label in response.label_annotations:
                if label.score > 0.5:
                    labels.append({
                        'description': label.description,
                        'score': label.score
                    })
            
            logger.info(f"Extracted {len(labels)} labels from image")
            return labels
            
        except Exception as e:
            logger.error(f"Error in Vision API label detection: {e}")
            return []
    
    def get_web_entities(self, image_base64: str, max_results: int = 5) -> List[Dict]:
        """
        Get web entities and similar products from image
        
        Args:
            image_base64: Base64 encoded image
            max_results: Maximum number of entities to return
            
        Returns:
            List of web entity dicts with 'description' and 'score'
        """
        if not self.client:
            logger.warning("Vision API client not initialized")
            return []
        
        try:
            # Decode base64 image
            image_content = base64.b64decode(image_base64)
            
            # Create Vision API image object
            image = vision.Image(content=image_content)
            
            # Perform web detection
            response = self.client.web_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            # Extract web entities
            entities = []
            if response.web_detection.web_entities:
                for entity in response.web_detection.web_entities[:max_results]:
                    if entity.score > 0.3 and entity.description:
                        entities.append({
                            'description': entity.description,
                            'score': entity.score
                        })
            
            logger.info(f"Extracted {len(entities)} web entities from image")
            return entities
            
        except Exception as e:
            logger.error(f"Error in Vision API web detection: {e}")
            return []
    
    def get_logos(self, image_base64: str) -> List[Dict]:
        """
        Detect brand logos in image
        
        Args:
            image_base64: Base64 encoded image
            
        Returns:
            List of logo dicts with 'description' and 'score'
        """
        if not self.client:
            logger.warning("Vision API client not initialized")
            return []
        
        try:
            # Decode base64 image
            image_content = base64.b64decode(image_base64)
            
            # Create Vision API image object
            image = vision.Image(content=image_content)
            
            # Perform logo detection
            response = self.client.logo_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            # Extract logos
            logos = []
            for logo in response.logo_annotations:
                if logo.score > 0.5 and logo.description:
                    logos.append({
                        'description': logo.description,
                        'score': logo.score
                    })
            
            logger.info(f"Detected {len(logos)} logos in image")
            return logos
            
        except Exception as e:
            logger.error(f"Error in Vision API logo detection: {e}")
            return []
    
    def get_text(self, image_base64: str) -> List[str]:
        """
        Extract text from image (for detecting brand names in text)
        
        Args:
            image_base64: Base64 encoded image
            
        Returns:
            List of text strings found in image
        """
        if not self.client:
            logger.warning("Vision API client not initialized")
            return []
        
        try:
            # Decode base64 image
            image_content = base64.b64decode(image_base64)
            
            # Create Vision API image object
            image = vision.Image(content=image_content)
            
            # Perform text detection
            response = self.client.text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            # Extract text
            texts = []
            if response.text_annotations:
                # First annotation contains full text
                if len(response.text_annotations) > 0:
                    full_text = response.text_annotations[0].description
                    texts = [t.strip() for t in full_text.split('\n') if t.strip()]
            
            logger.info(f"Extracted {len(texts)} text segments from image")
            return texts
            
        except Exception as e:
            logger.error(f"Error in Vision API text detection: {e}")
            return []
    
    def labels_to_search_query(self, labels: List[Dict]) -> str:
        """
        Convert labels to search query string
        
        Args:
            labels: List of label dicts
            
        Returns:
            Search query string
        """
        # Sort by score and take top labels
        sorted_labels = sorted(labels, key=lambda x: x['score'], reverse=True)
        descriptions = [label['description'] for label in sorted_labels[:5]]
        return ' '.join(descriptions)
    
    def labels_to_filters(self, labels: List[Dict]) -> List[str]:
        """
        Convert labels to filter strings for search
        Similar to Algolia optional filters in reference app
        
        Args:
            labels: List of label dicts
            
        Returns:
            List of filter strings
        """
        return [f"labels.description:'{label['description']}'" for label in labels]


# Singleton instance
_vision_service = None

def get_vision_service() -> VisionService:
    """Get or create VisionService singleton"""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service


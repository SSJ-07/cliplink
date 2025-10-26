"""
CLIP Visual Similarity Service
Uses CLIP (Contrastive Language-Image Pre-training) to verify product matches
by computing visual similarity between reel frames and product images
"""
import os
import logging
import io
import base64
from typing import List, Dict, Optional
import requests
from PIL import Image
import torch
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class CLIPService:
    """Service for CLIP-based visual similarity verification"""
    
    def __init__(self):
        """Initialize CLIP model"""
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._initialize_model()
    
    def _initialize_model(self):
        """Load CLIP model (lazy loading)"""
        try:
            logger.info("Loading CLIP model...")
            self.model = SentenceTransformer('clip-ViT-B-32')
            self.model.to(self.device)
            logger.info(f"CLIP model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Error loading CLIP model: {e}")
            self.model = None
    
    def get_image_embedding(self, image: Image.Image) -> Optional[np.ndarray]:
        """
        Get CLIP embedding for an image
        
        Args:
            image: PIL Image object
            
        Returns:
            Numpy array embedding or None if failed
        """
        if not self.model:
            logger.warning("CLIP model not initialized")
            return None
        
        try:
            # Ensure RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get embedding
            embedding = self.model.encode(
                image,
                convert_to_tensor=True,
                normalize_embeddings=True
            )
            
            return embedding.cpu().numpy()
            
        except Exception as e:
            logger.error(f"Error getting image embedding: {e}")
            return None
    
    def get_frame_embedding(self, frame_base64: str) -> Optional[np.ndarray]:
        """
        Get CLIP embedding from base64 encoded frame
        
        Args:
            frame_base64: Base64 encoded image
            
        Returns:
            Numpy array embedding or None if failed
        """
        try:
            # Decode base64
            image_bytes = base64.b64decode(frame_base64)
            image = Image.open(io.BytesIO(image_bytes))
            
            return self.get_image_embedding(image)
            
        except Exception as e:
            logger.error(f"Error getting frame embedding: {e}")
            return None
    
    def get_url_embedding(self, image_url: str, timeout: int = 5) -> Optional[np.ndarray]:
        """
        Get CLIP embedding from image URL
        
        Args:
            image_url: URL of the image
            timeout: Request timeout in seconds
            
        Returns:
            Numpy array embedding or None if failed
        """
        try:
            # Download image
            response = requests.get(
                image_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to download image from {image_url}")
                return None
            
            # Open image
            image = Image.open(io.BytesIO(response.content))
            
            return self.get_image_embedding(image)
            
        except Exception as e:
            logger.error(f"Error getting URL embedding from {image_url}: {e}")
            return None
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Convert to torch tensors
            emb1 = torch.from_numpy(embedding1).to(self.device)
            emb2 = torch.from_numpy(embedding2).to(self.device)
            
            # Compute cosine similarity
            similarity = torch.nn.functional.cosine_similarity(
                emb1.unsqueeze(0),
                emb2.unsqueeze(0)
            ).item()
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0
    
    def verify_products(
        self,
        frame_base64: str,
        products: List[Dict],
        min_similarity: float = 0.4,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Verify products against video frame using CLIP similarity
        
        Args:
            frame_base64: Base64 encoded frame from video
            products: List of product dicts with 'image_url' field
            min_similarity: Minimum similarity threshold
            max_results: Maximum number of results to return
            
        Returns:
            List of products with similarity scores, sorted by score
        """
        if not self.model:
            logger.warning("CLIP model not available, returning products without verification")
            # Return products with default similarity
            for product in products:
                product['visual_similarity'] = 0.5
            return products[:max_results]
        
        logger.info(f"Verifying {len(products)} products with CLIP...")
        
        # Get frame embedding
        frame_embedding = self.get_frame_embedding(frame_base64)
        if frame_embedding is None:
            logger.error("Could not get frame embedding")
            return products[:max_results]
        
        # Score each product
        scored_products = []
        for product in products:
            image_url = product.get('image_url', '')
            
            if not image_url:
                logger.warning(f"Product '{product.get('title', 'Unknown')}' has no image URL")
                continue
            
            # Get product image embedding
            product_embedding = self.get_url_embedding(image_url)
            
            if product_embedding is None:
                logger.warning(f"Could not get embedding for {image_url}")
                continue
            
            # Compute similarity
            similarity = self.compute_similarity(frame_embedding, product_embedding)
            
            # Add similarity score to product
            product['visual_similarity'] = round(similarity, 3)
            
            # Only keep products above threshold
            if similarity >= min_similarity:
                scored_products.append(product)
                logger.info(f"✓ {product.get('title', 'Unknown')[:50]}... - Similarity: {similarity:.3f}")
            else:
                logger.info(f"✗ {product.get('title', 'Unknown')[:50]}... - Similarity: {similarity:.3f} (below threshold)")
        
        # Sort by similarity
        scored_products.sort(key=lambda x: x['visual_similarity'], reverse=True)
        
        logger.info(f"CLIP verification: {len(scored_products)}/{len(products)} products passed threshold")
        
        return scored_products[:max_results]
    
    def verify_best_frame(
        self,
        frames: List[str],
        products: List[Dict],
        min_similarity: float = 0.4,
        max_results: int = 5
    ) -> tuple[List[Dict], int]:
        """
        Try multiple frames and use the one with best matches
        
        Args:
            frames: List of base64 encoded frames
            products: List of product dicts
            min_similarity: Minimum similarity threshold
            max_results: Maximum results to return
            
        Returns:
            Tuple of (best_products, frame_index_used)
        """
        best_products = []
        best_frame_idx = 0
        best_avg_score = 0.0
        
        for idx, frame in enumerate(frames):
            logger.info(f"Testing frame {idx+1}/{len(frames)}...")
            
            verified = self.verify_products(
                frame,
                products.copy(),  # Copy to avoid modifying original
                min_similarity,
                max_results
            )
            
            if verified:
                avg_score = sum(p['visual_similarity'] for p in verified) / len(verified)
                logger.info(f"Frame {idx+1} avg similarity: {avg_score:.3f}")
                
                if avg_score > best_avg_score:
                    best_avg_score = avg_score
                    best_products = verified
                    best_frame_idx = idx
        
        logger.info(f"Best frame: {best_frame_idx+1} with avg similarity: {best_avg_score:.3f}")
        return best_products, best_frame_idx


# Singleton instance
_clip_service = None

def get_clip_service() -> CLIPService:
    """Get or create CLIPService singleton"""
    global _clip_service
    if _clip_service is None:
        _clip_service = CLIPService()
    return _clip_service


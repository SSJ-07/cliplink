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
import numpy as np

# Optional imports - gracefully handle missing dependencies (for Vercel)
try:
    import torch
    from sentence_transformers import SentenceTransformer
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    torch = None
    SentenceTransformer = None
    logging.warning("CLIP dependencies (torch, sentence-transformers) not available. CLIP features disabled.")

logger = logging.getLogger(__name__)


class CLIPService:
    """Service for CLIP-based visual similarity verification"""
    
    def __init__(self):
        """Initialize CLIP model"""
        self.model = None
        if not CLIP_AVAILABLE:
            logger.warning("CLIP not available - visual similarity will be disabled")
            self.device = "cpu"
            return
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._initialize_model()
    
    def _initialize_model(self):
        """Load CLIP model (lazy loading)"""
        if not CLIP_AVAILABLE:
            logger.warning("CLIP dependencies not available")
            return
            
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
    
    def get_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get CLIP embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array embedding or None if failed
        """
        if not self.model:
            logger.warning("CLIP model not initialized")
            return None
        
        try:
            # Get embedding
            embedding = self.model.encode(
                text,
                convert_to_tensor=True,
                normalize_embeddings=True
            )
            
            return embedding.cpu().numpy()
            
        except Exception as e:
            logger.error(f"Error getting text embedding: {e}")
            return None
    
    def select_best_frames(
        self,
        frames: List[str],
        user_text: str,
        top_k: int = 2
    ) -> List[tuple[str, float, int]]:
        """
        Select top-k frames that best match user text using CLIP
        
        Args:
            frames: List of base64 encoded frames
            user_text: User's text description
            top_k: Number of top frames to return
            
        Returns:
            List of (frame_base64, similarity_score, frame_index)
        """
        if not CLIP_AVAILABLE or not self.model:
            logger.warning("CLIP model not available for frame selection, using heuristic")
            # Return first/middle frames with default scores
            if not frames:
                return []
            # Prefer middle frames over first/last
            if len(frames) == 1:
                return [(frames[0], 1.0, 0)]
            elif len(frames) == 2:
                return [(frames[0], 0.8, 0), (frames[1], 1.0, 1)]
            else:
                # Return first, middle, last
                mid = len(frames) // 2
                return [(frames[0], 0.7, 0), (frames[mid], 1.0, mid)][:top_k]
        
        if not user_text or not user_text.strip():
            logger.info("No user text provided, returning first frames")
            return [(frames[i], 1.0, i) for i in range(min(top_k, len(frames)))]
        
        logger.info(f"Selecting best {top_k} frames from {len(frames)} for text: '{user_text}'")
        
        try:
            # Get text embedding
            text_embedding = self.get_text_embedding(user_text)
            if text_embedding is None:
                logger.warning("Could not get text embedding, returning first frames")
                return [(frames[i], 0.5, i) for i in range(min(top_k, len(frames)))]
            
            # Get embeddings for all frames and compute similarity
            frame_scores = []
            for idx, frame in enumerate(frames):
                frame_embedding = self.get_frame_embedding(frame)
                
                if frame_embedding is None:
                    logger.warning(f"Could not get embedding for frame {idx+1}")
                    frame_scores.append((frame, 0.0, idx))
                    continue
                
                # Compute similarity
                similarity = self.compute_similarity(text_embedding, frame_embedding)
                frame_scores.append((frame, similarity, idx))
                logger.info(f"Frame {idx+1} similarity to '{user_text}': {similarity:.3f}")
            
            # Sort by similarity (descending) and return top-k
            frame_scores.sort(key=lambda x: x[1], reverse=True)
            selected = frame_scores[:top_k]
            
            logger.info(f"Selected frames: {[(idx+1, f'{score:.3f}') for _, score, idx in selected]}")
            return selected
            
        except Exception as e:
            logger.error(f"Error selecting frames: {e}", exc_info=True)
            # Fallback to first frames
            return [(frames[i], 0.5, i) for i in range(min(top_k, len(frames)))]
    
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


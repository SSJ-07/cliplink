"""
Product Ranking Service
Multi-factor ranking using visual similarity, text similarity, and brand matching
"""
import logging
from typing import List, Dict, Optional
import numpy as np
from services.clip_service import CLIPService

logger = logging.getLogger(__name__)


class ProductRankingService:
    """Service for ranking products by visual + text similarity + brand match"""
    
    # Scoring weights
    WEIGHT_VISUAL = 0.45
    WEIGHT_TEXT = 0.35
    WEIGHT_BRAND = 0.20
    
    def __init__(self):
        """Initialize ranking service"""
        pass
    
    def rank_products(
        self,
        selected_frames: List[str],
        query_pack: Dict,
        candidates: List[Dict],
        clip_service: CLIPService
    ) -> List[Dict]:
        """
        Rank products by multi-factor scoring
        
        Args:
            selected_frames: List of base64 encoded frames (top matches to user text)
            query_pack: Structured product info extracted from frame
            candidates: List of product candidate dicts
            clip_service: CLIP service for embeddings
            
        Returns:
            Ranked list of products with final scores
        """
        logger.info(f"Ranking {len(candidates)} candidates using visual + text + brand scoring")
        
        if not candidates:
            return []
        
        # Get query pack text for text similarity
        query_text = self._build_query_text(query_pack)
        logger.info(f"Query text for matching: '{query_text}'")
        
        # Get text embedding for query
        query_text_embedding = None
        try:
            from openai import OpenAI
            import os
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.embeddings.create(
                input=query_text,
                model="text-embedding-3-small"
            )
            query_text_embedding = np.array(response.data[0].embedding)
            logger.info("Got OpenAI embedding for query text")
        except Exception as e:
            logger.warning(f"Could not get OpenAI embedding: {e}")
        
        # Score each candidate
        scored_products = []
        for idx, candidate in enumerate(candidates):
            try:
                product_url = candidate.get('product_url', '')
                product_title = candidate.get('title', '')
                product_image_url = candidate.get('image_url', '')
                
                logger.info(f"Scoring candidate {idx+1}/{len(candidates)}: {product_title[:50]}...")
                
                # 1. Visual similarity score (CLIP)
                visual_score = self._compute_visual_score(
                    selected_frames,
                    product_image_url,
                    clip_service
                )
                
                # 2. Text similarity score (OpenAI embeddings)
                text_score = self._compute_text_score(
                    candidate,
                    query_text_embedding
                )
                
                # 3. Brand/domain match score
                brand_score = self._compute_brand_score(
                    candidate,
                    query_pack.get('brand', '')
                )
                
                # Calculate final weighted score
                final_score = (
                    self.WEIGHT_VISUAL * visual_score +
                    self.WEIGHT_TEXT * text_score +
                    self.WEIGHT_BRAND * brand_score
                )
                
                # Add scores to candidate
                candidate['visual_similarity'] = round(visual_score, 3)
                candidate['text_similarity'] = round(text_score, 3)
                candidate['brand_match'] = round(brand_score, 3)
                candidate['final_score'] = round(final_score, 3)
                candidate['similarity_score'] = round(final_score, 3)  # For backward compatibility
                
                scored_products.append(candidate)
                
                logger.info(f"  Visual: {visual_score:.3f}, Text: {text_score:.3f}, Brand: {brand_score:.3f}, Final: {final_score:.3f}")
                
            except Exception as e:
                logger.error(f"Error scoring candidate: {e}")
                # Add with default scores
                candidate['visual_similarity'] = 0.0
                candidate['text_similarity'] = 0.0
                candidate['brand_match'] = 0.0
                candidate['final_score'] = 0.0
                candidate['similarity_score'] = 0.0
                scored_products.append(candidate)
        
        # Sort by final score (descending)
        scored_products.sort(key=lambda x: x['final_score'], reverse=True)
        
        logger.info(f"Top 3 scores: {[p['final_score'] for p in scored_products[:3]]}")
        return scored_products
    
    def _compute_visual_score(
        self,
        selected_frames: List[str],
        product_image_url: str,
        clip_service: CLIPService
    ) -> float:
        """Compute visual similarity between frames and product image"""
        if not product_image_url or not selected_frames:
            return 0.0
        
        try:
            # Get product image embedding
            product_embedding = clip_service.get_url_embedding(product_image_url)
            if product_embedding is None:
                return 0.0
            
            # Compare with all selected frames, take max similarity
            max_similarity = 0.0
            for frame in selected_frames:
                frame_embedding = clip_service.get_frame_embedding(frame)
                if frame_embedding is None:
                    continue
                
                similarity = clip_service.compute_similarity(frame_embedding, product_embedding)
                max_similarity = max(max_similarity, similarity)
            
            return max_similarity
            
        except Exception as e:
            logger.warning(f"Error computing visual score: {e}")
            return 0.0
    
    def _compute_text_score(
        self,
        candidate: Dict,
        query_embedding: Optional[np.ndarray]
    ) -> float:
        """Compute text similarity between query and product"""
        if query_embedding is None:
            # Fallback to simple keyword matching
            return 0.5
        
        try:
            # Build product text
            product_text = f"{candidate.get('title', '')} {candidate.get('description', '')}"
            
            if not product_text.strip():
                return 0.0
            
            # Get product text embedding
            from openai import OpenAI
            import os
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.embeddings.create(
                input=product_text[:500],  # Limit length
                model="text-embedding-3-small"
            )
            product_embedding = np.array(response.data[0].embedding)
            
            # Compute cosine similarity
            similarity = np.dot(query_embedding, product_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(product_embedding)
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.warning(f"Error computing text score: {e}")
            return 0.5
    
    def _compute_brand_score(self, candidate: Dict, detected_brand: str) -> float:
        """Compute brand/domain match score"""
        if not detected_brand:
            return 0.5  # Neutral if no brand detected
        
        product_url = candidate.get('product_url', '').lower()
        product_title = candidate.get('title', '').lower()
        source = candidate.get('source', '').lower()
        
        detected_brand_lower = detected_brand.lower().replace(' ', '')
        
        # Check if brand is in URL (official site)
        if detected_brand_lower in product_url:
            logger.info(f"Brand '{detected_brand}' found in URL - official site")
            return 1.0
        
        # Check if brand is in title
        if detected_brand_lower in product_title:
            logger.info(f"Brand '{detected_brand}' found in title")
            return 0.8
        
        # Check if from trusted retailers
        trusted_retailers = ['amazon', 'walmart', 'target', 'ebay', 'bestbuy']
        for retailer in trusted_retailers:
            if retailer in product_url or retailer in source:
                logger.info(f"Trusted retailer: {retailer}")
                return 0.6
        
        # Default
        return 0.4
    
    def _build_query_text(self, query_pack: Dict) -> str:
        """Build query text from query pack for embedding"""
        parts = []
        
        if query_pack.get('brand'):
            parts.append(query_pack['brand'])
        if query_pack.get('model_guess'):
            parts.append(query_pack['model_guess'])
        if query_pack.get('product_type'):
            parts.append(query_pack['product_type'])
        if query_pack.get('colors'):
            parts.extend(query_pack['colors'][:2])
        if query_pack.get('attributes'):
            parts.extend(query_pack['attributes'][:2])
        if query_pack.get('user_text'):
            parts.append(query_pack['user_text'])
        
        return ' '.join(parts)


# Singleton instance
_product_ranking_service = None

def get_product_ranking_service() -> ProductRankingService:
    """Get or create ProductRankingService singleton"""
    global _product_ranking_service
    if _product_ranking_service is None:
        _product_ranking_service = ProductRankingService()
    return _product_ranking_service

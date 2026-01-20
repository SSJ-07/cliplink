"""
Frame Selection Service
Selects best frames matching user text using heuristics and Vision API labels
(No CLIP/torch dependencies)
"""
import logging
from typing import List, Tuple, Optional
from services.vision_service import VisionService

logger = logging.getLogger(__name__)


class FrameSelectionService:
    """Service for selecting best frames using heuristics and Vision API"""
    
    def __init__(self):
        """Initialize frame selection service"""
        pass
    
    def select_best_frames(
        self,
        frames: List[str],
        user_text: str,
        vision_service: Optional[VisionService] = None,
        top_k: int = 2
    ) -> List[Tuple[str, float, int]]:
        """
        Select top-k frames that best match user text using heuristics and Vision API
        
        Args:
            frames: List of base64 encoded frames
            user_text: User's text description
            vision_service: Vision service for label extraction (optional)
            top_k: Number of top frames to return
            
        Returns:
            List of (frame_base64, similarity_score, frame_index)
            Scores are heuristic-based (0.0-1.0)
        """
        if not frames:
            return []
        
        if not user_text or not user_text.strip():
            logger.info("No user text provided, returning first frames")
            # Return first frames with high scores
            return [(frames[i], 1.0, i) for i in range(min(top_k, len(frames)))]
        
        logger.info(f"Selecting best {top_k} frames from {len(frames)} for text: '{user_text}'")
        
        user_text_lower = user_text.lower()
        
        # Strategy 1: Use Vision API to extract labels and match with user text
        if vision_service:
            frame_scores = self._select_with_vision_api(
                frames, user_text_lower, vision_service
            )
        else:
            # Strategy 2: Simple heuristic (first, middle, last frames)
            frame_scores = self._select_with_heuristics(frames, user_text_lower)
        
        # Sort by score (descending)
        frame_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k
        selected = frame_scores[:top_k]
        logger.info(f"Selected frames: {[(i, f'{s:.3f}') for _, s, i in selected]}")
        return selected
    
    def _select_with_vision_api(
        self,
        frames: List[str],
        user_text: str,
        vision_service: VisionService
    ) -> List[Tuple[str, float, int]]:
        """
        Select frames using Vision API labels
        
        Args:
            frames: List of base64 encoded frames
            user_text: User's text (lowercase)
            vision_service: Vision service
            
        Returns:
            List of (frame_base64, score, frame_index)
        """
        frame_scores = []
        
        # Extract keywords from user text
        user_keywords = set(user_text.split())
        
        for idx, frame in enumerate(frames):
            try:
                # Get labels from Vision API
                labels = vision_service.get_image_labels(frame, max_results=10)
                
                # Calculate match score based on label overlap
                score = 0.0
                if labels:
                    label_descriptions = ' '.join([
                        l['description'].lower() 
                        for l in labels[:5]  # Top 5 labels
                    ])
                    
                    # Count keyword matches
                    matches = sum(
                        1 for keyword in user_keywords 
                        if keyword in label_descriptions or label_descriptions.find(keyword) >= 0
                    )
                    
                    # Score based on matches (normalized to 0-1)
                    if matches > 0:
                        score = min(1.0, matches / len(user_keywords) + 0.3)
                    else:
                        # No direct matches, but check for partial matches
                        for label in labels[:3]:
                            label_lower = label['description'].lower()
                            for keyword in user_keywords:
                                if keyword in label_lower or label_lower in keyword:
                                    score = max(score, 0.4)
                                    break
                
                # Add small bonus for later frames (usually more relevant)
                position_bonus = min(0.1, idx * 0.05 / len(frames))
                score = min(1.0, score + position_bonus)
                
                frame_scores.append((frame, score, idx))
                
            except Exception as e:
                logger.warning(f"Error processing frame {idx} with Vision API: {e}")
                # Default score for failed frames
                frame_scores.append((frame, 0.3, idx))
        
        return frame_scores
    
    def _select_with_heuristics(
        self,
        frames: List[str],
        user_text: str
    ) -> List[Tuple[str, float, int]]:
        """
        Select frames using simple heuristics (no API calls)
        
        Args:
            frames: List of base64 encoded frames
            user_text: User's text (lowercase, unused but kept for API consistency)
            
        Returns:
            List of (frame_base64, score, frame_index)
        """
        frame_scores = []
        
        for idx, frame in enumerate(frames):
            # Simple heuristic: prefer middle frames over first/last
            # First frame: 0.7, Middle frames: 1.0, Last frame: 0.8
            if len(frames) == 1:
                score = 1.0
            elif idx == 0:
                score = 0.7
            elif idx == len(frames) - 1:
                score = 0.8
            else:
                # Middle frames get highest score
                score = 1.0
            
            frame_scores.append((frame, score, idx))
        
        return frame_scores


# Singleton instance
_frame_selection_service = None

def get_frame_selection_service() -> FrameSelectionService:
    """Get or create FrameSelectionService singleton"""
    global _frame_selection_service
    if _frame_selection_service is None:
        _frame_selection_service = FrameSelectionService()
    return _frame_selection_service

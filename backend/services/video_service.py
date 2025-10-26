"""
Video processing service for Instagram Reels
Handles video download and frame extraction with Instagram auth support
"""
import os
import logging
import tempfile
import base64
from typing import List, Optional
from moviepy.editor import VideoFileClip
import yt_dlp
import subprocess
import shutil

logger = logging.getLogger(__name__)


class VideoService:
    """Service for video download and frame extraction"""
    
    def __init__(self):
        """Initialize video service"""
        self.temp_dir = tempfile.gettempdir()
    
    def download_reel(self, reel_url: str) -> Optional[str]:
        """
        Download Instagram reel or TikTok video with multiple fallback strategies
        
        Args:
            reel_url: URL of the reel/video
            
        Returns:
            Path to downloaded video file or None if failed
        """
        # Strategy 1: Try with browser cookies for Instagram
        if "instagram.com" in reel_url:
            video_path = self._download_with_cookies(reel_url)
            if video_path:
                return video_path
        
        # Strategy 2: Standard yt-dlp download
        try:
            output_path = os.path.join(self.temp_dir, f"reel_{os.urandom(8).hex()}.mp4")
            
            ydl_opts = {
                'outtmpl': output_path,
                'format': 'best[height<=720]',  # Limit quality for faster processing
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([reel_url])
            
            if os.path.exists(output_path):
                logger.info(f"Successfully downloaded video to {output_path}")
                return output_path
            else:
                logger.error("Video file not created after download")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading reel: {e}")
            return None
    
    def _download_with_cookies(self, reel_url: str) -> Optional[str]:
        """Try downloading with browser cookies"""
        try:
            output_path = os.path.join(self.temp_dir, f"reel_{os.urandom(8).hex()}.mp4")
            
            # Try Chrome first, then Firefox
            for browser in ['chrome', 'firefox', 'safari']:
                try:
                    ydl_opts = {
                        'outtmpl': output_path,
                        'format': 'best[height<=720]',
                        'cookiesfrombrowser': (browser,),
                        'quiet': True,
                        'no_warnings': True,
                        'noplaylist': True,
                        'extract_flat': False,
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([reel_url])
                    
                    if os.path.exists(output_path):
                        logger.info(f"Successfully downloaded with {browser} cookies")
                        return output_path
                        
                except Exception as e:
                    logger.warning(f"Failed with {browser} cookies: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading with cookies: {e}")
            return None
    
    def _capture_frame_screenshot(self, reel_url: str) -> Optional[str]:
        """Capture frame using headless browser screenshot"""
        try:
            # Check if playwright is available
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                logger.warning("Playwright not available for screenshot fallback")
                return None
            
            frame_path = os.path.join(self.temp_dir, f"frame_{os.urandom(8).hex()}.jpg")
            
            with sync_playwright() as p:
                browser = p.firefox.launch(headless=True)
                page = browser.new_page()
                
                # Set viewport to mobile size (Instagram reels are mobile-first)
                page.set_viewport_size({"width": 375, "height": 667})
                
                # Navigate to the reel
                page.goto(reel_url, wait_until="networkidle", timeout=30000)
                
                # Wait for video to load
                page.wait_for_timeout(3000)
                
                # Take screenshot
                page.screenshot(path=frame_path, full_page=False)
                browser.close()
            
            if os.path.exists(frame_path):
                logger.info(f"Successfully captured frame screenshot: {frame_path}")
                return frame_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
    
    def extract_frames(
        self,
        video_path: str,
        num_frames: int = 3,
        start_offset: float = 1.0
    ) -> List[str]:
        """
        Extract multiple frames from video at intervals
        
        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract
            start_offset: Seconds to skip at beginning
            
        Returns:
            List of base64 encoded frame images
        """
        frames = []
        clip = None
        
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            
            # Calculate frame extraction times
            # Skip first and last second, distribute frames evenly
            usable_duration = duration - start_offset - 1.0
            if usable_duration <= 0:
                usable_duration = duration * 0.8
                start_offset = duration * 0.1
            
            if num_frames == 1:
                times = [start_offset + usable_duration / 2]
            else:
                interval = usable_duration / (num_frames - 1) if num_frames > 1 else 0
                times = [start_offset + i * interval for i in range(num_frames)]
            
            # Extract frames
            for i, time in enumerate(times):
                if time >= duration:
                    time = duration - 0.5
                
                try:
                    # Save frame to temporary file
                    frame_path = os.path.join(
                        self.temp_dir,
                        f"frame_{os.urandom(4).hex()}_{i}.jpg"
                    )
                    
                    clip.save_frame(frame_path, t=time)
                    
                    # Read and encode as base64
                    with open(frame_path, 'rb') as f:
                        frame_data = base64.b64encode(f.read()).decode('utf-8')
                        frames.append(frame_data)
                    
                    # Clean up frame file
                    os.unlink(frame_path)
                    
                except Exception as e:
                    logger.error(f"Error extracting frame at {time}s: {e}")
            
            logger.info(f"Extracted {len(frames)} frames from video")
            
        except Exception as e:
            logger.error(f"Error in frame extraction: {e}")
        
        finally:
            if clip:
                clip.close()
        
        return frames
    
    def extract_single_frame(
        self,
        video_path: str,
        time: float = 1.0
    ) -> Optional[str]:
        """
        Extract a single frame from video
        
        Args:
            video_path: Path to video file
            time: Time in seconds to extract frame
            
        Returns:
            Base64 encoded frame image or None
        """
        frames = self.extract_frames(video_path, num_frames=1, start_offset=time)
        return frames[0] if frames else None
    
    def cleanup_video(self, video_path: str):
        """
        Clean up downloaded video file
        
        Args:
            video_path: Path to video file
        """
        try:
            if video_path and os.path.exists(video_path):
                os.unlink(video_path)
                logger.info(f"Cleaned up video file: {video_path}")
        except Exception as e:
            logger.error(f"Error cleaning up video: {e}")
    
    def process_reel(
        self,
        reel_url: str,
        num_frames: int = 3
    ) -> List[str]:
        """
        Complete workflow: download reel and extract frames with fallbacks
        
        Args:
            reel_url: URL of the reel
            num_frames: Number of frames to extract
            
        Returns:
            List of base64 encoded frames
        """
        video_path = None
        
        try:
            # Strategy 1: Download video
            video_path = self.download_reel(reel_url)
            
            if video_path:
                # Extract frames from video
                frames = self.extract_frames(video_path, num_frames=num_frames)
                if frames:
                    logger.info(f"Successfully extracted {len(frames)} frames from video")
                    return frames
            
            # Strategy 2: Screenshot fallback for Instagram
            if "instagram.com" in reel_url:
                logger.info("Video download failed, trying screenshot fallback...")
                screenshot_path = self._capture_frame_screenshot(reel_url)
                
                if screenshot_path:
                    # Convert screenshot to base64
                    try:
                        with open(screenshot_path, 'rb') as f:
                            image_data = f.read()
                            base64_data = base64.b64encode(image_data).decode('utf-8')
                        
                        # Clean up screenshot
                        os.unlink(screenshot_path)
                        
                        logger.info("Successfully captured frame via screenshot")
                        return [base64_data]
                        
                    except Exception as e:
                        logger.error(f"Error processing screenshot: {e}")
                        if os.path.exists(screenshot_path):
                            os.unlink(screenshot_path)
            
            logger.error("All frame extraction strategies failed")
            return []
            
        finally:
            # Always cleanup video
            if video_path:
                self.cleanup_video(video_path)


# Singleton instance
_video_service = None

def get_video_service() -> VideoService:
    """Get or create VideoService singleton"""
    global _video_service
    if _video_service is None:
        _video_service = VideoService()
    return _video_service


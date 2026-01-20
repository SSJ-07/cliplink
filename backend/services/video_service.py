"""
Video processing service for Instagram Reels
Handles video download and frame extraction with Instagram auth support
"""
import os
import logging
import tempfile
import base64
from typing import List, Optional
import yt_dlp
import subprocess
import shutil
import json

# Optional import - gracefully handle missing moviepy (for Vercel)
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    VideoFileClip = None
    logging.warning("moviepy not available. Will use ffmpeg fallback for frame extraction.")

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
        # Log yt-dlp version and Python environment
        import sys
        import shutil
        try:
            logger.info(f"Python executable: {sys.executable}")
            logger.info(f"yt-dlp version: {yt_dlp.version.__version__}")
            logger.info(f"yt-dlp path: {shutil.which('yt-dlp')}")
            logger.info(f"ffmpeg path: {shutil.which('ffmpeg')}")
            logger.info(f"ffprobe path: {shutil.which('ffprobe')}")
        except Exception as e:
            logger.warning(f"Could not log environment info: {e}")
        
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
                'format': 'best[ext=mp4]/best',  # More flexible format selection
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([reel_url])

            exists = os.path.exists(output_path)

            # #region agent log
            try:
                log_payload = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H_download",
                    "location": "video_service.py:download_reel:after_yt_dlp",
                    "message": "yt_dlp download attempt finished",
                    "data": {
                        "reel_url_prefix": str(reel_url)[:64],
                        "output_path_exists": exists
                    },
                    "timestamp": __import__("time").time()
                }
                with open("/Users/sumedhjadhav/Documents/Projects/cliplink/.cursor/debug.log", "a") as _f:
                    _f.write(json.dumps(log_payload) + "\n")
            except Exception:
                pass
            # #endregion

            if exists:
                # Log file details
                file_size = os.path.getsize(output_path)
                logger.info(f"Successfully downloaded video to {output_path}")
                logger.info(f"Downloaded file size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
                
                # Try to get video info with ffprobe
                try:
                    import subprocess
                    result = subprocess.run(
                        ['ffprobe', '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', output_path],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        import json as json_module
                        probe_data = json_module.loads(result.stdout)
                        duration = float(probe_data.get('format', {}).get('duration', 0))
                        logger.info(f"Video duration: {duration:.2f} seconds")
                        logger.info(f"Video format: {probe_data.get('format', {}).get('format_name', 'unknown')}")
                    else:
                        logger.warning(f"ffprobe failed: {result.stderr}")
                except Exception as e:
                    logger.warning(f"Could not probe video info: {e}")
                
                return output_path
            else:
                logger.error("Video file not created after download")
                return None

        except Exception as e:
            logger.error(f"Error downloading reel: {e}")

            # #region agent log
            try:
                log_payload = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H_download_error",
                    "location": "video_service.py:download_reel:exception",
                    "message": "Exception during yt_dlp download",
                    "data": {
                        "reel_url_prefix": str(reel_url)[:64],
                        "error_type": type(e).__name__,
                        "error_str": str(e)[:200]
                    },
                    "timestamp": __import__("time").time()
                }
                with open("/Users/sumedhjadhav/Documents/Projects/cliplink/.cursor/debug.log", "a") as _f:
                    _f.write(json.dumps(log_payload) + "\n")
            except Exception:
                pass
            # #endregion

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
                        'format': 'best[ext=mp4]/best',  # More flexible format selection
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
    
    def _extract_frames_ffmpeg(self, video_path: str, num_frames: int = 3) -> List[str]:
        """
        Fallback frame extraction using ffmpeg directly
        
        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract
            
        Returns:
            List of base64 encoded frame images
        """
        frames = []
        temp_dir = tempfile.mkdtemp()
        
        try:
            logger.info(f"Using ffmpeg fallback for frame extraction")
            
            # Get video duration first
            probe_cmd = [
                'ffprobe', '-v', 'error', '-show_entries',
                'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip()) if result.returncode == 0 else 10.0
            logger.info(f"Video duration from ffprobe: {duration:.2f}s")
            
            # Calculate frame times
            if duration < 10:
                # For short videos, extract frames at equal intervals
                start = 0.5
                end = duration - 0.5
                interval = (end - start) / (num_frames - 1) if num_frames > 1 else 0
                times = [start + i * interval for i in range(num_frames)]
            else:
                # For longer videos, skip first and last second
                start = 1.0
                end = duration - 1.0
                interval = (end - start) / (num_frames - 1) if num_frames > 1 else 0
                times = [start + i * interval for i in range(num_frames)]
            
            logger.info(f"Extracting frames at times: {[f'{t:.2f}s' for t in times]}")
            
            # Extract each frame
            for i, time in enumerate(times):
                output_path = os.path.join(temp_dir, f"frame_{i:03d}.jpg")
                cmd = [
                    'ffmpeg', '-hide_banner', '-loglevel', 'error',
                    '-ss', str(time),
                    '-i', video_path,
                    '-frames:v', '1',
                    '-vf', 'scale=640:-1',
                    '-q:v', '2',
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(output_path):
                    # Read and encode as base64
                    with open(output_path, 'rb') as f:
                        frame_data = base64.b64encode(f.read()).decode('utf-8')
                        frames.append(frame_data)
                    logger.info(f"Frame {i+1} extracted successfully at {time:.2f}s")
                else:
                    logger.error(f"Failed to extract frame {i+1} at {time:.2f}s: {result.stderr}")
            
            logger.info(f"FFmpeg fallback extracted {len(frames)} frames")
            return frames
            
        except Exception as e:
            logger.error(f"Error in ffmpeg frame extraction: {e}", exc_info=True)
            return frames
        finally:
            # Clean up temp directory
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
    
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
        
        logger.info(f"Starting frame extraction from {video_path}")
        logger.info(f"Requested frames: {num_frames}, start_offset: {start_offset}")
        
        # Check if file exists and log size
        if not os.path.exists(video_path):
            logger.error(f"Video file does not exist: {video_path}")
            return frames
        
        file_size = os.path.getsize(video_path)
        logger.info(f"Video file size: {file_size} bytes")

        # Try moviepy first if available, otherwise use ffmpeg directly
        if not MOVIEPY_AVAILABLE:
            logger.info("moviepy not available, using ffmpeg fallback")
            return self._extract_frames_ffmpeg(video_path, num_frames)

        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            logger.info(f"Video loaded successfully. Duration: {duration:.2f} seconds")
            
            # Calculate frame extraction times
            # Adjust offsets based on video duration
            if duration < 10:
                # For short videos (< 10s), use minimal offsets
                start_offset = 0.5
                end_offset = 0.5
                logger.info(f"Short video detected. Using minimal offsets: start={start_offset}s, end={end_offset}s")
            else:
                # For longer videos, use standard offsets
                start_offset = 1.0
                end_offset = 1.0
            
            # Calculate usable duration
            usable_duration = duration - start_offset - end_offset
            if usable_duration <= 0:
                logger.warning(f"Video too short even with minimal offsets (duration={duration}s). Using fallback.")
                # Fallback: extract frames from the middle portion
                start_offset = duration * 0.1
                usable_duration = duration * 0.8
                logger.info(f"Fallback: start_offset={start_offset:.2f}, usable_duration={usable_duration:.2f}")
            
            if num_frames == 1:
                times = [start_offset + usable_duration / 2]
            else:
                interval = usable_duration / (num_frames - 1) if num_frames > 1 else 0
                times = [start_offset + i * interval for i in range(num_frames)]
            
            # Extract frames
            logger.info(f"Extracting frames at times: {[f'{t:.2f}s' for t in times]}")
            for i, time in enumerate(times):
                if time >= duration:
                    time = duration - 0.5
                    logger.warning(f"Frame {i+1} time adjusted to {time:.2f}s (was beyond duration)")
                
                try:
                    # Save frame to temporary file
                    frame_path = os.path.join(
                        self.temp_dir,
                        f"frame_{os.urandom(4).hex()}_{i}.jpg"
                    )
                    
                    clip.save_frame(frame_path, t=time)
                    
                    # Check if frame was created
                    if not os.path.exists(frame_path):
                        logger.error(f"Frame file not created at {frame_path}")
                        continue
                    
                    frame_size = os.path.getsize(frame_path)
                    logger.info(f"Frame {i+1} saved: {frame_path} ({frame_size} bytes)")
                    
                    # Read and encode as base64
                    with open(frame_path, 'rb') as f:
                        frame_data = base64.b64encode(f.read()).decode('utf-8')
                        frames.append(frame_data)
                    
                    # Clean up frame file
                    os.unlink(frame_path)
                    
                except Exception as e:
                    logger.error(f"Error extracting frame at {time}s: {e}")
            
            logger.info(f"Successfully extracted {len(frames)} frames from video")

        except Exception as e:
            logger.error(f"Error in frame extraction: {e}", exc_info=True)

        finally:
            if clip:
                clip.close()
        
        # If moviepy failed and we have no frames, try ffmpeg fallback
        if not frames:
            logger.warning("MoviePy extraction failed, trying ffmpeg fallback")
            frames = self._extract_frames_ffmpeg(video_path, num_frames)
        
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
        
        logger.info(f"Starting process_reel for URL: {reel_url}")
        logger.info(f"Requested number of frames: {num_frames}")

        try:
            # Strategy 1: Download video
            video_path = self.download_reel(reel_url)

            # #region agent log
            try:
                log_payload = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H_process_download",
                    "location": "video_service.py:process_reel:after_download",
                    "message": "download_reel completed",
                    "data": {
                        "reel_url_prefix": str(reel_url)[:64],
                        "got_video_path": bool(video_path)
                    },
                    "timestamp": __import__("time").time()
                }
                with open("/Users/sumedhjadhav/Documents/Projects/cliplink/.cursor/debug.log", "a") as _f:
                    _f.write(json.dumps(log_payload) + "\n")
            except Exception:
                pass
            # #endregion

            if video_path:
                logger.info(f"Video downloaded successfully: {video_path}")
                # Extract frames from video
                frames = self.extract_frames(video_path, num_frames=num_frames)
                if frames:
                    logger.info(f"Successfully extracted {len(frames)} frames from video")

                    # #region agent log
                    try:
                        log_payload = {
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "H_process_frames_ok",
                            "location": "video_service.py:process_reel:frames_ok",
                            "message": "Frames extracted successfully",
                            "data": {
                                "frames_extracted": len(frames)
                            },
                            "timestamp": __import__("time").time()
                        }
                        with open("/Users/sumedhjadhav/Documents/Projects/cliplink/.cursor/debug.log", "a") as _f:
                            _f.write(json.dumps(log_payload) + "\n")
                    except Exception:
                        pass
                    # #endregion

                    return frames
                else:
                    logger.warning("Frame extraction returned empty list")
            
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

            # #region agent log
            try:
                log_payload = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H_all_failed",
                    "location": "video_service.py:process_reel:all_failed",
                    "message": "All frame extraction strategies failed",
                    "data": {
                        "reel_url_prefix": str(reel_url)[:64]
                    },
                    "timestamp": __import__("time").time()
                }
                with open("/Users/sumedhjadhav/Documents/Projects/cliplink/.cursor/debug.log", "a") as _f:
                    _f.write(json.dumps(log_payload) + "\n")
            except Exception:
                pass
            # #endregion

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

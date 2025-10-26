"""
Quick test script to verify video frame extraction works
"""
import sys
sys.path.append('.')

from services.video_service import get_video_service
from dotenv import load_dotenv

load_dotenv()

# Test video extraction
video_service = get_video_service()

# Test with an Instagram Reel URL
test_url = input("Enter Instagram Reel URL (or press Enter for text-only mode): ")

if test_url:
    print("\n🎥 Downloading and extracting frames...")
    frames = video_service.process_reel(test_url, num_frames=3)
    
    if frames:
        print(f"✅ Successfully extracted {len(frames)} frames!")
        print(f"   Frame 1 size: {len(frames[0])} bytes (base64)")
        if len(frames) > 1:
            print(f"   Frame 2 size: {len(frames[1])} bytes (base64)")
        if len(frames) > 2:
            print(f"   Frame 3 size: {len(frames[2])} bytes (base64)")
        
        # Optionally save first frame to see it
        import base64
        with open("test_frame.jpg", "wb") as f:
            f.write(base64.b64decode(frames[0]))
        print("\n💾 Saved first frame as test_frame.jpg")
    else:
        print("❌ Failed to extract frames")
else:
    print("Skipped video test")


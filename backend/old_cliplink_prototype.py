# -*- coding: utf-8 -*-
"""
⚠️  ARCHIVED / DEPRECATED ⚠️

This is the OLD prototype version of ClipLink.
It has been replaced by the new implementation in:
  - backend/app.py (main API)
  - backend/services/vision_service.py (Google Vision API)
  - backend/services/video_service.py (video processing)
  - backend/services/product_search_service.py (product search)

The new version is better because:
  ✅ Extracts 3 frames (vs 1)
  ✅ Uses Google Vision API (cheaper than GPT-4o)
  ✅ Has product database with embeddings
  ✅ Vector similarity search
  ✅ Production-ready Flask API

Keep this file for historical reference only.
DO NOT USE IN PRODUCTION.

Original Colab notebook:
https://colab.research.google.com/drive/1JSLLvNopYnwloQpGurpTEjOjn-DpwmCK
"""

# Commented out - this was for Jupyter/Colab only
# !pip install openai yt-dlp moviepy

import openai
import base64
import json
import os
from moviepy.editor import VideoFileClip
# from IPython.display import display  # Not needed - Jupyter only
# from PIL import Image  # Not used
# import requests  # Not used
import yt_dlp

# 🔐 OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")  # Load from environment variable

def download_instagram_reel(reel_url: str, out_path: str = "reel.mp4"):
    ydl_opts = {
        'outtmpl': out_path,
        'format': 'mp4',
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([reel_url])
    return out_path

def extract_frame_base64(video_path: str, t: float = 1.0):
    clip = VideoFileClip(video_path)
    frame_path = "frame.jpg"
    clip.save_frame(frame_path, t=t)
    with open(frame_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def query_gpt4o(b64_image: str, shopper_note: str):
    prompt = f"""
You are a fashion shopping assistant.

A user saw this frame in a reel. Their note is: '{shopper_note}'.

Return a JSON like this:
{{
  "primaryLink": "<exact or very close product, if possible>",
  "altLink": "<close alternate under $60>"
}}

Be concise. If the exact product is unclear, return two close public options with links from Amazon, Asos, or other common sites.
Only output valid JSON.
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful shopping assistant."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
            ]}
        ],
        temperature=0.3
    )

    msg = response.choices[0].message.content
    try:
        return json.loads(msg)
    except:
        return {"error": "Could not parse JSON", "raw": msg}

# ========================================
# MAIN SCRIPT - COMMENTED OUT
# Use the new API instead: python app.py
# ========================================

# Uncomment below to run this old version (not recommended)
"""
reel_url = input("Enter the Instagram Reel URL: ")
note = input("Describe what you're looking for in the reel: ")

# ⬇️ Download reel and extract frame
video_path = download_instagram_reel(reel_url)
b64 = extract_frame_base64(video_path)

# 🧠 Get product links
result = query_gpt4o(b64, note)
print(result)
"""

if __name__ == "__main__":
    print("=" * 60)
    print("⚠️  This is the OLD archived version of ClipLink")
    print("=" * 60)
    print("\n❌ This script is deprecated and should not be used.\n")
    print("✅ Use the NEW implementation instead:")
    print("   1. Run: python app.py")
    print("   2. Use API endpoint: POST /api/analyze-reel")
    print("\n📖 See README.md for setup instructions\n")
    print("=" * 60)


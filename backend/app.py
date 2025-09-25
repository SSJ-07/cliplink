from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import base64
import json
import os
import tempfile
from moviepy.editor import VideoFileClip
import yt_dlp
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

def download_instagram_reel(reel_url: str, out_path: str = None):
    """Download Instagram reel and return the path to the video file"""
    if out_path is None:
        out_path = tempfile.mktemp(suffix=".mp4")
    
    ydl_opts = {
        'outtmpl': out_path,
        'format': 'best[height<=720]',  # Limit quality for faster processing
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([reel_url])
        return out_path
    except Exception as e:
        logger.error(f"Error downloading reel: {e}")
        # Return a mock response for testing
        return None

def extract_frame_base64(video_path: str, t: float = 1.0):
    """Extract a frame from video and return as base64"""
    try:
        clip = VideoFileClip(video_path)
        frame_path = tempfile.mktemp(suffix=".jpg")
        clip.save_frame(frame_path, t=t)
        clip.close()
        
        with open(frame_path, "rb") as f:
            frame_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Clean up temporary files
        os.unlink(frame_path)
        return frame_data
    except Exception as e:
        logger.error(f"Error extracting frame: {e}")
        raise

def query_gpt4o(b64_image: str, shopper_note: str):
    """Query GPT-4o with image and shopping note"""
    prompt = f"""
You are a fashion shopping assistant.

A user saw this frame in a reel. Their note is: '{shopper_note}'.

Return a JSON like this:
{{
  "primarySku": "<product identifier or name>",
  "primaryLink": "<exact or very close product, if possible>",
  "altLinks": ["<close alternate under $60>", "<another alternative>"]
}}

Be concise. If the exact product is unclear, return two close public options with links from Amazon, Asos, or other common sites.
Only output valid JSON.
"""
    
    try:
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
        except json.JSONDecodeError:
            return {"error": "Could not parse JSON", "raw": msg}
    except Exception as e:
        logger.error(f"Error querying GPT-4o: {e}")
        raise

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Backend is running"})

@app.route('/api/analyze-reel', methods=['POST'])
def analyze_reel():
    """Analyze Instagram reel and find products"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        reel_url = data.get('url')
        note = data.get('note', '')
        
        if not reel_url:
            return jsonify({"error": "URL is required"}), 400
        
        logger.info(f"Processing reel: {reel_url}")
        
        # For now, return a mock response to test the flow
        # TODO: Implement actual video processing
        mock_result = {
            "primarySku": "NIKE-AIR-MAX-270",
            "primaryLink": "https://www.nike.com/t/air-max-270-mens-shoes-KkLcGR",
            "altLinks": [
                "https://www.amazon.com/Nike-Air-Max-270-Sneaker/dp/B07B4L1QB3",
                "https://www.footlocker.com/product/nike-air-max-270-mens/55088016.html"
            ]
        }
        
        return jsonify(mock_result)
        
    except Exception as e:
        logger.error(f"Error in analyze_reel: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint for frontend connection"""
    return jsonify({
        "message": "Backend is connected!",
        "status": "success",
        "data": {
            "primarySku": "TEST-PRODUCT-123",
            "primaryLink": "https://example.com/test-product",
            "altLinks": [
                "https://example.com/alt1",
                "https://example.com/alt2"
            ]
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)


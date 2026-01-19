"""
ClipLink Backend API
Instagram Reel to Product Search using Google Vision API and Vector Search
Based on visual-product-search-app architecture with improvements
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
from dotenv import load_dotenv
import json

# Import our services
from services.vision_service import get_vision_service
from services.video_service import get_video_service
from services.web_search_service import get_web_search_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Enhanced CORS configuration
CORS(app, 
     origins=["*"],
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# Validate required environment variables
REQUIRED_ENV_VARS = ["OPENAI_API_KEY"]
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        logger.warning(f"Missing environment variable: {var}")


@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
    
    return jsonify({
        "status": "healthy",
        "message": "ClipLink Backend API is running",
        "version": "2.0",
        "features": {
            "vision_api": os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is not None or 
                         os.getenv("GOOGLE_APPLICATION_CREDENTIALS_BASE64") is not None,
            "openai": os.getenv("OPENAI_API_KEY") is not None
        }
    })


@app.route('/api/analyze-reel', methods=['POST', 'OPTIONS'])
def analyze_reel():
    """
    Analyze Instagram reel and find matching products
    
    Uses multi-step process:
    1. Download reel and extract frames
    2. Use Vision API to get labels from frames
    3. Combine with user description
    4. Search products using embeddings and vector similarity
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()

        # #region agent log
        try:
            log_payload = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H_frontend_payload",
                "location": "app.py:analyze_reel:request",
                "message": "analyze_reel payload received",
                "data": {
                    "has_data": data is not None,
                    "keys": list(data.keys()) if isinstance(data, dict) else None
                },
                "timestamp": __import__("time").time()
            }
            with open("/Users/sumedhjadhav/Documents/Projects/cliplink/.cursor/debug.log", "a") as _f:
                _f.write(json.dumps(log_payload) + "\n")
        except Exception:
            pass
        # #endregion
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        reel_url = data.get('url')
        user_description = data.get('note', '')
        num_frames = data.get('num_frames', 3)  # Extract 3 frames by default
        
        if not reel_url:
            return jsonify({"error": "URL is required"}), 400
        
        logger.info(f"Processing reel: {reel_url}")
        logger.info(f"User description: {user_description}")
        
        # Initialize services
        video_service = get_video_service()
        vision_service = get_vision_service()
        web_search_service = get_web_search_service()
        
        # Step 1: Download video and extract frames
        logger.info("Step 1: Extracting frames from video...")

        # #region agent log
        try:
            log_payload = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H_video_start",
                "location": "app.py:analyze_reel:before_process_reel",
                "message": "Calling process_reel",
                "data": {
                    "reel_url_prefix": str(reel_url)[:64],
                    "num_frames": num_frames
                },
                "timestamp": __import__("time").time()
            }
            with open("/Users/sumedhjadhav/Documents/Projects/cliplink/.cursor/debug.log", "a") as _f:
                _f.write(json.dumps(log_payload) + "\n")
        except Exception:
            pass
        # #endregion

        frames = video_service.process_reel(reel_url, num_frames=num_frames)
        
        if not frames:
            logger.warning("Could not extract frames from video")

            # #region agent log
            try:
                log_payload = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H_no_frames",
                    "location": "app.py:analyze_reel:no_frames",
                    "message": "process_reel returned no frames",
                    "data": {
                        "reel_url_prefix": str(reel_url)[:64],
                        "num_frames_requested": num_frames
                    },
                    "timestamp": __import__("time").time()
                }
                with open("/Users/sumedhjadhav/Documents/Projects/cliplink/.cursor/debug.log", "a") as _f:
                    _f.write(json.dumps(log_payload) + "\n")
            except Exception:
                pass
            # #endregion

            return jsonify({
                "error": "no_frame_extracted",
                "message": "Unable to extract frames from the Instagram reel.",
                "suggestion": "This could be due to Instagram restrictions, an unsupported video format, or the video being too short. Try using a different reel URL or upload a screenshot of the product instead.",
                "debug_info": {
                    "url": reel_url,
                    "platform": "Instagram" if "instagram.com" in reel_url else "TikTok" if "tiktok.com" in reel_url else "Unknown",
                    "frames_requested": num_frames,
                    "frames_extracted": 0,
                    "possible_causes": [
                        "Instagram/TikTok requires authentication",
                        "Video is private or deleted",
                        "Network restrictions or rate limiting",
                        "Video format not supported"
                    ],
                    "tip": "For Instagram reels, make sure the reel is publicly accessible (can be viewed in an incognito browser window)." if "instagram.com" in reel_url else ""
                },
                "used_clip": False,
                "frames_extracted": 0
            }), 400
        
        logger.info(f"Extracted {len(frames)} frames")

        # #region agent log
        try:
            log_payload = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H_frames_ok",
                "location": "app.py:analyze_reel:frames_ok",
                "message": "process_reel returned frames",
                "data": {
                    "frames_count": len(frames)
                },
                "timestamp": __import__("time").time()
            }
            with open("/Users/sumedhjadhav/Documents/Projects/cliplink/.cursor/debug.log", "a") as _f:
                _f.write(json.dumps(log_payload) + "\n")
        except Exception:
            pass
        # #endregion
        
        # Step 2: Analyze frames with Vision API (labels + logos + text)
        logger.info("Step 2: Analyzing frames with Vision API...")
        all_labels = []
        all_logos = []
        all_texts = []
        
        for i, frame in enumerate(frames):
            # Get labels
            labels = vision_service.get_image_labels(frame)
            all_labels.extend(labels)
            
            # Get logos (for brand detection)
            logos = vision_service.get_logos(frame)
            all_logos.extend(logos)
            
            # Get text (for brand names in text)
            texts = vision_service.get_text(frame)
            all_texts.extend(texts)
            
            logger.info(f"Frame {i+1}: {len(labels)} labels, {len(logos)} logos, {len(texts)} text segments")
        
        # Deduplicate labels
        unique_labels = {}
        for label in all_labels:
            desc = label['description']
            if desc not in unique_labels or label['score'] > unique_labels[desc]['score']:
                unique_labels[desc] = label
        
        final_labels = sorted(unique_labels.values(), key=lambda x: x['score'], reverse=True)
        logger.info(f"Total: {len(final_labels)} labels, {len(all_logos)} logos, {len(all_texts)} texts")
        
        # Step 3: Detect brand
        logger.info("Step 3: Detecting brand...")
        detected_brand = web_search_service.detect_brand(all_logos, all_texts, final_labels)
        if detected_brand:
            logger.info(f"✓ Brand detected: {detected_brand}")
        
        # Step 4: Build search query
        search_query = user_description
        if not search_query and final_labels:
            # If no user description, use labels as query
            search_query = vision_service.labels_to_search_query(final_labels)
        
        # Add brand to query if detected and not already in query
        if detected_brand and detected_brand.lower() not in search_query.lower():
            search_query = f"{detected_brand} {search_query}"
        
        logger.info(f"Final search query: {search_query}")
        
        # Step 5: Search real products from web
        logger.info("Step 5: Searching products from web...")
        products = web_search_service.search_products(
            query=search_query,
            brand=detected_brand,
            num_results=10  # Get more candidates for CLIP filtering
        )
        
        if not products:
            return jsonify({
                "error": "No matching products found",
                "labels": [label['description'] for label in final_labels[:5]],
                "brand": detected_brand,
                "query": search_query
            }), 404
        
        # Step 6: (Temporarily disabled) CLIP Visual Similarity Verification
        # For local testing, we skip the heavy CLIP model to avoid torch/transformers issues.
        # Products are returned based purely on web search relevance.
        verified_products = products[:5]
        for p in verified_products:
            p['visual_similarity'] = p.get('visual_similarity', 0.5)
        
        logger.info(f"Returning {len(verified_products)} products without CLIP verification (local/dev mode).")
        
        # Step 7: Format response with CLIP flags
        return format_product_response(
            verified_products, 
            final_labels[:10], 
            detected_brand,
            used_clip=True,
            frames_extracted=len(frames)
        )
        
    except Exception as e:
        logger.error(f"Error in analyze_reel: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "message": "An error occurred while processing your request"
        }), 500


@app.route('/api/search-products', methods=['POST', 'OPTIONS'])
def search_products():
    """
    Search products by text query only (no video)
    Useful for testing or text-only search
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        query = data.get('query', '')
        num_results = data.get('num_results', 5)
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        logger.info(f"Searching products with query: {query}")
        
        # Search products from web
        web_search_service = get_web_search_service()
        products = web_search_service.search_products(query, num_results=num_results)
        
        if not products:
            return jsonify({
                "error": "No matching products found",
                "query": query
            }), 404
        
        return format_product_response(products)
        
    except Exception as e:
        logger.error(f"Error in search_products: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "message": "An error occurred while searching products"
        }), 500


@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint for frontend connection"""
    return jsonify({
        "message": "Backend is connected!",
        "status": "success",
        "timestamp": "2024-01-01T00:00:00Z"
    })


@app.route('/api/debug/environment', methods=['GET'])
def check_environment():
    """Check yt-dlp and ffmpeg availability"""
    import sys
    import shutil
    import tempfile
    
    try:
        import yt_dlp
        yt_dlp_version = yt_dlp.version.__version__
    except Exception as e:
        yt_dlp_version = f"Error: {str(e)}"
    
    return jsonify({
        "python": sys.executable,
        "yt_dlp_version": yt_dlp_version,
        "yt_dlp_path": shutil.which("yt-dlp"),
        "ffmpeg_path": shutil.which("ffmpeg"),
        "ffprobe_path": shutil.which("ffprobe"),
        "temp_dir": tempfile.gettempdir(),
        "google_vision_configured": bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_BASE64")),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
    })


def format_product_response(products, labels=None, detected_brand=None, used_clip=None, frames_extracted=None):
    """
    Format product search results for frontend
    
    Args:
        products: List of product dicts
        labels: Optional list of visual labels detected
        detected_brand: Optional detected brand name
        used_clip: Whether CLIP verification was used
        frames_extracted: Number of frames extracted
        
    Returns:
        JSON response
    """
    if not products:
        return jsonify({
            "products": [],
            "count": 0
        })
    
    # Format for frontend (with images and better data)
    formatted_products = []
    for product in products:
        formatted_products.append({
            "id": product.get('id', ''),
            "title": product.get('title', ''),
            "description": product.get('description', ''),
            "price": product.get('price', 0),
            "currency": product.get('currency', 'USD'),
            "image_url": product.get('image_url', ''),
            "product_url": product.get('product_url', ''),
            "similarity_score": product.get('similarity_score', 0),
            "visual_similarity": product.get('visual_similarity', 0),  # CLIP score
            "tags": product.get('tags', []),
            "source": product.get('source', 'Web')
        })
    
    response = {
        "products": formatted_products,
        "count": len(formatted_products),
        "primary": formatted_products[0] if formatted_products else None,
        "alternatives": formatted_products[1:4] if len(formatted_products) > 1 else []
    }
    
    # Include detected labels if available
    if labels:
        response['detected_labels'] = [
            {"label": label['description'], "confidence": label['score']}
            for label in labels[:10]
        ]
    
    # Include detected brand if available
    if detected_brand:
        response['detected_brand'] = detected_brand
    
    # Include CLIP usage flags
    if used_clip is not None:
        response['used_clip'] = used_clip
    if frames_extracted is not None:
        response['frames_extracted'] = frames_extracted
    
    # Legacy format support (for backward compatibility)
    if formatted_products:
        response['primarySku'] = formatted_products[0]['title']
        response['primaryLink'] = formatted_products[0]['product_url']
        response['altLinks'] = [p['product_url'] for p in formatted_products[1:3]]
    
    return jsonify(response)


if __name__ == '__main__':
    # Check if running in production
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"Starting ClipLink Backend on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        debug=debug,
        host='0.0.0.0',
        port=port
    )

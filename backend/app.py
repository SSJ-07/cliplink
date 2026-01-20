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
from services.clip_service import get_clip_service
from services.frame_understanding_service import get_frame_understanding_service
from services.product_ranking_service import get_product_ranking_service

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
        
        # NEW PIPELINE: 4-Stage Visual Product Search
        
        # Initialize all services
        clip_service = get_clip_service()
        frame_understanding_service = get_frame_understanding_service()
        product_ranking_service = get_product_ranking_service()
        
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
        
        # NEW PIPELINE: 4-Stage Visual Product Search
        
        # Stage 1: Select best frames matching user text
        logger.info("Stage 1: Selecting best frames matching user description...")
        selected_frames = clip_service.select_best_frames(
            frames,
            user_description,
            top_k=2  # Use top 2 frames
        )
        
        if not selected_frames:
            logger.warning("Frame selection failed, using all frames")
            selected_frames = [(frames[i], 1.0, i) for i in range(len(frames))]
        
        best_frame = selected_frames[0][0]
        best_frame_idx = selected_frames[0][2]
        logger.info(f"Selected frame {best_frame_idx+1} (similarity: {selected_frames[0][1]:.3f})")
        
        # Stage 2: Understand the selected frame
        logger.info("Stage 2: Understanding frame content...")
        query_pack = frame_understanding_service.understand_frame(
            best_frame,
            vision_service,
            user_description
        )
        
        # Stage 3: Search for product candidates
        logger.info("Stage 3: Searching for product candidates...")
        candidates = web_search_service.search_products_from_query_pack(
            query_pack,
            num_results=30
        )
        
        if not candidates:
            logger.warning("No product candidates found")
            return jsonify({
                "error": "No matching products found",
                "query_pack": query_pack,
                "suggestion": "Try using different keywords or a different reel"
            }), 404
        
        logger.info(f"Found {len(candidates)} product candidates")
        
        # Stage 4: Rank candidates by visual + text + brand similarity
        logger.info("Stage 4: Ranking products by visual similarity...")
        ranked_products = product_ranking_service.rank_products(
            [sf[0] for sf in selected_frames],
            query_pack,
            candidates,
            clip_service
        )
        
        # Return top 5 ranked products
        final_products = ranked_products[:5]
        logger.info(f"Returning top {len(final_products)} products")
        
        # Format response
        return format_product_response(
            final_products,
            query_pack.get('labels', [])[:10],
            query_pack.get('brand'),
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
        # Handle both dict format (from query pack) and list of strings
        if labels and isinstance(labels[0], dict):
            response['detected_labels'] = [
                {"label": label['description'], "confidence": label['score']}
                for label in labels[:10]
            ]
        else:
            # Labels is a list of strings
            response['detected_labels'] = [
                {"label": label, "confidence": 0.9}
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

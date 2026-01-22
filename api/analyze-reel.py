"""
Vercel serverless function for analyzing reels
Uses the ClipLink backend services for the 4-stage pipeline
"""
import sys
import os
import json

# Add backend to path so we can import services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from flask import Flask, jsonify, request as flask_request
import logging

# Import backend services
from services.video_service import get_video_service
from services.vision_service import get_vision_service
from services.web_search_service import get_web_search_service
from services.clip_service import get_clip_service
from services.frame_understanding_service import get_frame_understanding_service
from services.product_ranking_service import get_product_ranking_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_product_response(products, labels=None, detected_brand=None, used_clip=None, frames_extracted=None):
    """Format product response (matches backend/app.py format)"""
    formatted_products = []
    for product in products:
        formatted_products.append({
            'id': product.get('id', ''),
            'title': product.get('title', ''),
            'description': product.get('description', ''),
            'price': product.get('price', 0.0),
            'currency': product.get('currency', 'USD'),
            'image_url': product.get('image_url', ''),
            'product_url': product.get('product_url', ''),
            'similarity_score': product.get('similarity_score', 0),
            'visual_similarity': product.get('visual_similarity', 0),
            'tags': product.get('tags', []),
            'source': product.get('source', '')
        })
    
    response = {
        "products": formatted_products,
        "count": len(formatted_products),
        "primary": formatted_products[0] if formatted_products else None,
        "alternatives": formatted_products[1:4] if len(formatted_products) > 1 else []
    }
    
    if labels:
        if labels and isinstance(labels[0], dict):
            response['detected_labels'] = [
                {"label": label['description'], "confidence": label['score']}
                for label in labels[:10]
            ]
        else:
            response['detected_labels'] = [
                {"label": label, "confidence": 0.9}
                for label in labels[:10]
            ]
    
    if detected_brand:
        response['detected_brand'] = detected_brand
    
    if used_clip is not None:
        response['used_clip'] = used_clip
    if frames_extracted is not None:
        response['frames_extracted'] = frames_extracted
    
    if formatted_products:
        response['primarySku'] = formatted_products[0]['title']
        response['primaryLink'] = formatted_products[0]['product_url']
        response['altLinks'] = [p['product_url'] for p in formatted_products[1:3]]
    
    return response


# Create Flask app for request handling
app = Flask(__name__)

@app.route('/api/analyze-reel', methods=['POST', 'OPTIONS'])
def analyze_reel_route():
    """Flask route handler for analyze-reel"""
    return analyze_reel_logic()

def analyze_reel_logic():
    """Core logic for analyzing reels"""
    try:
        if flask_request.method == 'OPTIONS':
            return ('', 200, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            })
        
        if flask_request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405
        
        data = flask_request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        reel_url = data.get('url')
        user_description = data.get('note', '')
        num_frames = data.get('num_frames', 3)
        
        if not reel_url:
            return jsonify({"error": "URL is required"}), 400
        
        logger.info(f"Processing reel: {reel_url}")
        logger.info(f"User description: {user_description}")
        
        # Initialize services
        video_service = get_video_service()
        vision_service = get_vision_service()
        web_search_service = get_web_search_service()
        clip_service = get_clip_service()
        frame_understanding_service = get_frame_understanding_service()
        product_ranking_service = get_product_ranking_service()
        
        # Stage 1: Extract frames from video
        logger.info("Stage 1: Extracting frames from video...")
        frames = video_service.process_reel(reel_url, num_frames=num_frames)
        
        if not frames:
            logger.warning("Could not extract frames from video")
            return jsonify({
                "error": "no_frame_extracted",
                "message": "Unable to extract frames from the Instagram reel.",
                "suggestion": "Try using a different reel URL or ensure the reel is publicly accessible."
            }), 400
        
        logger.info(f"Extracted {len(frames)} frames")
        
        # Stage 2: Select best frames matching user text
        logger.info("Stage 2: Selecting best frames matching user description...")
        selected_frames = clip_service.select_best_frames(
            frames,
            user_description,
            top_k=2
        )
        
        if not selected_frames:
            logger.warning("Frame selection failed, using all frames")
            selected_frames = [(frames[i], 1.0, i) for i in range(len(frames))]
        
        best_frame = selected_frames[0][0]
        best_frame_idx = selected_frames[0][2]
        logger.info(f"Selected frame {best_frame_idx+1} (similarity: {selected_frames[0][1]:.3f})")
        
        # Stage 3: Understand the selected frame
        logger.info("Stage 3: Understanding frame content...")
        query_pack = frame_understanding_service.understand_frame(
            best_frame,
            vision_service,
            user_description
        )
        
        # Stage 4: Search for product candidates
        logger.info("Stage 4: Searching for product candidates...")
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
        
        # Stage 5: Rank candidates by visual + text + brand similarity
        logger.info("Stage 5: Ranking products by visual similarity...")
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
        response = format_product_response(
            final_products,
            query_pack.get('labels', [])[:10],
            query_pack.get('brand'),
            used_clip=True,
            frames_extracted=len(frames)
        )
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in analyze_reel: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "message": "An error occurred while processing your request"
        }), 500

def handler(vercel_request):
    """Vercel serverless function handler - converts Vercel request to Flask WSGI"""
    from werkzeug.wrappers import Request, Response
    from werkzeug.serving import WSGIRequestHandler
    
    # Convert Vercel request to Werkzeug request
    environ = {
        'REQUEST_METHOD': vercel_request.get('method', 'GET'),
        'PATH_INFO': vercel_request.get('path', '/api/analyze-reel'),
        'QUERY_STRING': '',
        'CONTENT_TYPE': vercel_request.get('headers', {}).get('content-type', 'application/json'),
        'CONTENT_LENGTH': str(len(vercel_request.get('body', '') or '')),
        'wsgi.input': None,
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.errors': None,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
        'SERVER_NAME': 'vercel',
        'SERVER_PORT': '443',
        'HTTP_HOST': vercel_request.get('headers', {}).get('host', ''),
    }
    
    # Add headers
    for key, value in vercel_request.get('headers', {}).items():
        environ[f'HTTP_{key.upper().replace("-", "_")}'] = value
    
    # Handle body
    body = vercel_request.get('body', '') or ''
    if body:
        environ['wsgi.input'] = type('obj', (object,), {
            'read': lambda: body.encode() if isinstance(body, str) else body,
            'readline': lambda: b'',
            'readlines': lambda: []
        })()
    
    # Create Werkzeug request
    werkzeug_request = Request(environ)
    
    # Call Flask app
    with app.request_context(werkzeug_request.environ):
        response = app.full_dispatch_request()
    
    # Convert Flask response to Vercel format
    return {
        'statusCode': response.status_code,
        'headers': dict(response.headers),
        'body': response.get_data(as_text=True)
    }

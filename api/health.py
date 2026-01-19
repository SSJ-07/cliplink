"""
Vercel serverless function for health check
"""
from flask import jsonify

def handler(request):
    """Health check endpoint for Vercel"""
    return jsonify({
        "status": "healthy",
        "message": "ClipLink Backend API is running",
        "version": "2.0",
        "features": {
            "openai": True,
            "vision_api": False
        }
    })


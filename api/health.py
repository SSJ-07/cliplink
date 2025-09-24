from flask import jsonify

def handler(request):
    """Health check endpoint for Vercel"""
    return jsonify({
        "status": "healthy",
        "message": "Backend is running"
    })

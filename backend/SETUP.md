# Backend Setup Guide

## Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

### Required Variables

```bash
# OpenAI API Key (Required)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-api-key-here

# Google Cloud Vision API Credentials (Required)
# Option 1: Use credentials file path
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/google-credentials.json

# Option 2: Use base64 encoded credentials (for deployment)
# Run: base64 -i google-credentials.json | tr -d '\n'
# GOOGLE_APPLICATION_CREDENTIALS_BASE64=your-base64-encoded-json-here

# Flask Configuration
FLASK_ENV=development
PORT=5001
```

### Optional Variables

```bash
# Product Database Path (optional, defaults to sample products)
PRODUCT_DATABASE_PATH=/path/to/products.json
```

## Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Running the Backend

```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Run the Flask app
python app.py
```

The backend will start on `http://localhost:5001`

## API Endpoints

### Health Check
```bash
GET /api/health
```

### Analyze Reel
```bash
POST /api/analyze-reel
Content-Type: application/json

{
  "url": "https://www.instagram.com/reel/abc123/",
  "note": "I want the blue jacket",
  "num_frames": 3
}
```

### Search Products (Text Only)
```bash
POST /api/search-products
Content-Type: application/json

{
  "query": "blue running shoes",
  "top_k": 5
}
```

## Google Cloud Vision API Setup

1. Create a Google Cloud Project
2. Enable Cloud Vision API
3. Create a Service Account with "Cloud Vision API User" role
4. Download JSON credentials
5. Set path in .env file

See [SETUP_GUIDE.md](../SETUP_GUIDE.md) for detailed instructions.


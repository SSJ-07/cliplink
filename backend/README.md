# ClipLink Backend

Visual Product Search API for Instagram Reels using Google Vision AI and OpenAI Embeddings.

## Features

- 🎥 Instagram/TikTok video download and frame extraction
- 👁️ Google Cloud Vision API for image label detection
- 🧠 OpenAI embeddings for semantic product search
- 🔍 Vector similarity matching for accurate results
- 📦 Built-in sample product database

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Create a `.env` file:**
```bash
# Required
OPENAI_API_KEY=sk-your-openai-api-key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/google-credentials.json

# Optional
FLASK_ENV=development
PORT=5001
```

3. **Run the server:**
```bash
python app.py
```

Server will start at `http://localhost:5001`

## Environment Variables

### Required
- `OPENAI_API_KEY`: Your OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google Cloud Vision API credentials JSON file
  - Alternative: `GOOGLE_APPLICATION_CREDENTIALS_BASE64` (base64 encoded JSON for deployment)

### Optional
- `FLASK_ENV`: Environment mode (`development` or `production`)
- `PORT`: Server port (default: 5001)
- `PRODUCT_DATABASE_PATH`: Custom product database JSON file

## API Endpoints

### Health Check
```bash
GET /api/health
```

### Analyze Reel
```bash
POST /api/analyze-reel
{
  "url": "https://www.instagram.com/reel/xyz/",
  "note": "I want the blue shoes",
  "num_frames": 3
}
```

### Search Products
```bash
POST /api/search-products
{
  "query": "blue running shoes",
  "top_k": 5
}
```

## Architecture

```
Reel URL → Video Download → Frame Extraction → Vision API Analysis
    ↓
Labels + Description → Embeddings → Vector Search → Products
```

## Setup Guides

- 📖 [Detailed Setup Guide](SETUP.md)
- 🚀 [Main Setup Guide](../SETUP_GUIDE.md)

## Security Note

Never commit your `.env` file to version control. The `.env` file is already added to `.gitignore`.

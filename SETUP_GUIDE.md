# ClipLink Setup Guide

## Overview

ClipLink uses visual product search technology to find products from Instagram Reels. It combines:
- **Google Vision API** for image label detection
- **OpenAI Embeddings** for semantic search
- **Vector similarity** for product matching

## Architecture

### Backend Stack
- **Framework**: Flask (Python)
- **Vision AI**: Google Cloud Vision API
- **Embeddings**: OpenAI text-embedding-3-small
- **Video Processing**: yt-dlp + moviepy
- **Vector Search**: In-memory with scikit-learn (production: use Pinecone/Supabase Vector)

### Frontend Stack
- **Framework**: React + TypeScript + Vite
- **UI Library**: shadcn/ui + Tailwind CSS
- **Auth**: Firebase Authentication
- **State**: React hooks

## Setup Instructions

### Prerequisites

1. **Python 3.9+** installed
2. **Node.js 18+** installed
3. **Google Cloud Account** with Vision API enabled
4. **OpenAI API Account** with credits

### Step 1: Google Cloud Vision API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Cloud Vision API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Cloud Vision API"
   - Click "Enable"
4. Create Service Account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Name it (e.g., "cliplink-vision")
   - Grant role: "Cloud Vision API User"
   - Click "Done"
5. Create and download key:
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose JSON format
   - Save the downloaded file as `google-credentials.json`

### Step 2: OpenAI API Setup

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to [API Keys](https://platform.openai.com/api-keys)
4. Click "Create new secret key"
5. Copy and save the key (starts with `sk-`)

### Step 3: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables template
cp .env.example .env

# Edit .env file with your credentials
nano .env  # or use your preferred editor
```

**Edit `.env` file:**
```env
OPENAI_API_KEY=sk-your-actual-openai-key-here
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/google-credentials.json
FLASK_ENV=development
PORT=5001
```

**Test backend:**
```bash
# Run the backend server
python app.py

# In another terminal, test the health endpoint
curl http://localhost:5001/api/health
```

### Step 4: Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment variables template
cp .env.example .env.local

# Edit .env.local file
nano .env.local
```

**Edit `.env.local` file:**
```env
VITE_API_URL=http://localhost:5001
VITE_FIREBASE_API_KEY=your-firebase-key
VITE_FIREBASE_AUTH_DOMAIN=your-domain
VITE_FIREBASE_PROJECT_ID=your-project-id
# ... other Firebase config
```

**Run frontend:**
```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Testing the Feature

### Test 1: Health Check

```bash
curl http://localhost:5001/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "ClipLink Backend API is running",
  "version": "2.0",
  "features": {
    "vision_api": true,
    "openai": true
  }
}
```

### Test 2: Text-Only Product Search

```bash
curl -X POST http://localhost:5001/api/search-products \
  -H "Content-Type: application/json" \
  -d '{"query": "blue adidas running shoes"}'
```

### Test 3: Full Reel Analysis

1. Open ClipLink frontend in browser
2. Paste an Instagram Reel URL (e.g., `https://www.instagram.com/reel/ABC123/`)
3. Optionally add description: "I want the blue jacket"
4. Click "Find My Products"
5. View results with product images, prices, and links

## How It Works

### Workflow

```
User Input (Reel URL + Description)
    ↓
Download Video (yt-dlp)
    ↓
Extract 3 Frames (moviepy)
    ↓
Analyze Each Frame (Google Vision API)
    ↓
Extract Labels (e.g., "clothing", "denim", "jacket")
    ↓
Combine Labels + User Description
    ↓
Generate Embedding (OpenAI)
    ↓
Vector Similarity Search (cosine similarity)
    ↓
Return Top 5 Products
    ↓
Display with Images + Prices + Links
```

### Key Improvements Over Original

1. **Multiple Frame Analysis**: Extracts 3 frames instead of 1 for better accuracy
2. **Web Entity Detection**: Uses Vision API's web detection for brand identification
3. **Vector Embeddings**: Semantic search instead of keyword matching
4. **Tag Boosting**: Products with matching tags get higher scores
5. **Rich Product Data**: Full product info with images, prices, descriptions
6. **Better UI**: Product cards with images, match scores, and tags

## Deployment

### Backend Deployment (Vercel Serverless)

1. Create `vercel.json` in backend folder:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "OPENAI_API_KEY": "@openai-api-key",
    "GOOGLE_APPLICATION_CREDENTIALS_BASE64": "@google-credentials-base64"
  }
}
```

2. Convert Google credentials to base64:
```bash
base64 -i google-credentials.json | tr -d '\n' > google-credentials-base64.txt
```

3. Deploy:
```bash
vercel --prod
```

### Frontend Deployment (Vercel)

```bash
cd frontend
vercel --prod
```

Update `VITE_API_URL` in Vercel environment variables to your backend URL.

## Product Database

Currently uses sample products in `services/product_search_service.py`.

### To Add Real Products

Create `backend/data/products.json`:
```json
[
  {
    "id": "unique-id",
    "title": "Product Name",
    "description": "Product description with keywords",
    "tags": ["tag1", "tag2", "category"],
    "price": 99.99,
    "currency": "USD",
    "image_url": "https://...",
    "product_url": "https://..."
  }
]
```

### Production Database Options

1. **Supabase Vector**: Postgres with pgvector extension
2. **Pinecone**: Managed vector database
3. **Weaviate**: Open-source vector database
4. **Algolia**: Search as a service (like reference app)

## Troubleshooting

### Vision API not working

- Check credentials file path is absolute
- Verify Vision API is enabled in Google Cloud Console
- Check service account has correct permissions

### Video download fails

- Instagram/TikTok may block automated downloads
- Try updating yt-dlp: `pip install --upgrade yt-dlp`
- Use test endpoint to verify without video download

### No products found

- Check OpenAI API key is valid and has credits
- Verify product database is loaded
- Add more sample products to increase matches

### Frontend connection error

- Verify backend is running on correct port
- Check CORS is properly configured
- Verify `VITE_API_URL` is set correctly

## Cost Estimation

### Per Request Costs

- **Google Vision API**: $1.50 per 1000 images (3 frames = $0.0045)
- **OpenAI Embeddings**: $0.02 per 1M tokens (~50 words = $0.000001)
- **Total per request**: ~$0.005

### Free Tiers

- **Google Vision**: 1000 images/month free
- **OpenAI**: $5 free credits on new accounts
- **Vercel**: Generous free tier for hosting

## Next Steps

1. **Add More Products**: Populate database with real products
2. **Shopify Integration**: Connect to Shopify API like reference app
3. **Vector Database**: Move to production vector DB
4. **Caching**: Add Redis for frequently searched items
5. **Analytics**: Track search queries and matches
6. **Feedback Loop**: Let users rate match quality

## Support

For issues or questions:
1. Check logs: Backend logs show detailed error messages
2. Test each component separately (health check, text search, then full flow)
3. Verify all environment variables are set

## License

MIT License - feel free to use and modify for your projects.


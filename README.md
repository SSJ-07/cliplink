# ClipLink 🔗✨

> Transform Instagram Reels into shoppable product links using AI-powered visual search

ClipLink is an intelligent product discovery platform that analyzes Instagram Reels and TikTok videos to identify and recommend products featured in the content. Built with Google Cloud Vision AI and OpenAI embeddings for accurate product matching.

## ✨ Features

- 🎥 **Video Analysis**: Extracts multiple frames from Instagram Reels and TikTok videos
- 👁️ **Visual Recognition**: Uses Google Cloud Vision API to detect objects, clothing, and products
- 🧠 **Smart Search**: Combines visual labels with user descriptions for better results
- 🎯 **Vector Matching**: Semantic search using OpenAI embeddings and cosine similarity
- 🛍️ **Product Display**: Beautiful product cards with images, prices, and direct links
- 📊 **Match Scores**: Shows confidence scores for each product match
- 🏷️ **Tag Detection**: Displays detected labels and categories from video analysis

## 🏗️ Architecture

### Tech Stack

**Frontend**
- React + TypeScript + Vite
- shadcn/ui + Tailwind CSS
- Firebase Authentication
- Modern responsive design

**Backend**
- Flask (Python)
- Google Cloud Vision API
- OpenAI Embeddings (text-embedding-3-small)
- yt-dlp for video download
- moviepy for frame extraction
- scikit-learn for vector similarity

### How It Works

```
User Input: Reel URL + Description
         ↓
    Download Video (yt-dlp)
         ↓
    Extract 3 Frames (moviepy)
         ↓
    Analyze with Vision API
         ↓
    Detect: labels, colors, objects
         ↓
    Combine: Labels + User Text
         ↓
    Generate Embeddings (OpenAI)
         ↓
    Vector Similarity Search
         ↓
    Return Top 5 Products
         ↓
    Display with Rich UI
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Google Cloud account with Vision API enabled
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/cliplink.git
cd cliplink
```

2. **Setup Backend**
```bash
cd backend
pip install -r requirements.txt

# Create .env file
echo "OPENAI_API_KEY=your-key-here" > .env
echo "GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json" >> .env

# Run backend
python app.py
```

3. **Setup Frontend**
```bash
cd frontend
npm install

# Create .env.local file
echo "VITE_API_URL=http://localhost:5001" > .env.local

# Run frontend
npm run dev
```

4. **Open in browser**: http://localhost:5173

## 📖 Documentation

- 📘 [Complete Setup Guide](SETUP_GUIDE.md) - Detailed setup instructions
- 🔧 [Backend README](backend/README.md) - Backend API documentation
- 🎨 [Frontend README](frontend/README.md) - Frontend setup and development

## 🎯 Usage

1. **Get a Reel URL**: Copy link from Instagram or TikTok
2. **Paste in ClipLink**: Add the URL to the input field
3. **Describe (Optional)**: Add details like "I want the blue jacket"
4. **Find Products**: Click "Find My Products" button
5. **Browse Results**: See matched products with images, prices, and links
6. **Shop**: Click "Shop Now" to visit product pages

## 🛠️ API Endpoints

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
  "note": "I want the blue shoes",
  "num_frames": 3
}
```

Response:
```json
{
  "products": [
    {
      "id": "1",
      "title": "Nike Air Max 270",
      "description": "Running shoes...",
      "price": 150.00,
      "currency": "USD",
      "image_url": "https://...",
      "product_url": "https://...",
      "similarity_score": 0.92,
      "tags": ["shoes", "nike", "running"]
    }
  ],
  "detected_labels": [
    {"label": "Footwear", "confidence": 0.95},
    {"label": "Shoe", "confidence": 0.93}
  ]
}
```

## 🔧 Configuration

### Environment Variables

**Backend (.env)**
```bash
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
FLASK_ENV=development
PORT=5001
```

**Frontend (.env.local)**
```bash
VITE_API_URL=http://localhost:5001
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
```

## 📊 Product Database

Currently uses sample products. To add real products:

1. Create `backend/data/products.json`
2. Format:
```json
[
  {
    "id": "unique-id",
    "title": "Product Name",
    "description": "Description with keywords",
    "tags": ["category", "brand", "type"],
    "price": 99.99,
    "currency": "USD",
    "image_url": "https://...",
    "product_url": "https://..."
  }
]
```

### Production Database Options

- **Supabase Vector**: PostgreSQL with pgvector
- **Pinecone**: Managed vector database
- **Algolia**: Search as a service (like reference implementation)
- **Weaviate**: Open-source vector database

## 🚀 Deployment

### Backend (Vercel/Railway)

```bash
cd backend
vercel --prod
```

Set environment variables:
- `OPENAI_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS_BASE64` (base64 encoded JSON)

### Frontend (Vercel/Netlify)

```bash
cd frontend
npm run build
vercel --prod
```

Update `VITE_API_URL` to your backend URL.

## 💰 Cost Estimation

Per request costs:
- Google Vision API: ~$0.0045 (3 frames)
- OpenAI Embeddings: ~$0.000001
- **Total**: ~$0.005 per search

Free tiers:
- Google Vision: 1000 images/month
- OpenAI: $5 credits for new accounts
- Vercel: Generous free hosting tier

## 🎓 Inspired By

Based on the architecture of [visual-product-search-app](https://github.com/IliasHad/visual-product-search-app) by IliasHad, with significant improvements:

### Key Enhancements
- ✅ Multiple frame extraction (3 vs 1)
- ✅ Vector embeddings for semantic search
- ✅ Tag boosting for better accuracy
- ✅ Rich product data with images
- ✅ Modern UI with product cards
- ✅ Match confidence scores
- ✅ Label detection display

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Google Cloud Vision API for image analysis
- OpenAI for embeddings API
- shadcn/ui for beautiful components
- IliasHad for the original visual-product-search-app concept

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Made with ❤️ for product discovery enthusiasts

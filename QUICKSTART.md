# ClipLink Quick Start Guide

Get ClipLink running in 5 minutes!

## Prerequisites

- Python 3.9+ and pip
- Node.js 18+ and npm
- Google Cloud account
- OpenAI API key

## Step 1: Get API Keys

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy it (starts with `sk-`)

### Google Vision API
1. Go to https://console.cloud.google.com/
2. Create project → Enable "Cloud Vision API"
3. IAM & Admin → Service Accounts → Create
4. Add role: "Cloud Vision API User"
5. Keys → Add Key → Create (JSON)
6. Download the JSON file

## Step 2: Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-your-key-here
GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/google-credentials.json
FLASK_ENV=development
PORT=5001
EOF

# Copy your Google credentials file to backend/
# Then run:
python app.py
```

Backend runs at http://localhost:5001

## Step 3: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
echo "VITE_API_URL=http://localhost:5001" > .env.local

# Run dev server
npm run dev
```

Frontend runs at http://localhost:5173

## Step 4: Test It!

1. Open http://localhost:5173
2. Login with your credentials
3. Paste an Instagram Reel URL
4. Add description: "I want the shoes"
5. Click "Find My Products"
6. See results! 🎉

## Quick Test Without Frontend

```bash
# Test health
curl http://localhost:5001/api/health

# Test text search
curl -X POST http://localhost:5001/api/search-products \
  -H "Content-Type: application/json" \
  -d '{"query":"blue shoes"}'
```

## Troubleshooting

### Backend won't start
- Check `.env` file exists
- Verify Python 3.9+: `python --version`
- Check credentials path is absolute

### Vision API error
- Verify API is enabled in Google Cloud Console
- Check credentials file is valid JSON
- Ensure service account has correct role

### Frontend can't connect
- Backend must be running on port 5001
- Check `VITE_API_URL` in `.env.local`
- CORS is configured to allow all origins

### No products found
- Sample products are included by default
- Check OpenAI API key is valid
- Try text-only search first

## Next Steps

- Read [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed configuration
- Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for architecture
- Add your own products in `backend/data/products.json`

## Need Help?

1. Check backend logs for errors
2. Test each endpoint separately
3. Verify all environment variables are set
4. See [SETUP_GUIDE.md](SETUP_GUIDE.md) troubleshooting section

---

Happy product searching! 🛍️


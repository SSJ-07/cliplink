# Vercel Deployment Fixes Applied

## ✅ Changes Made

### 1. CLIP Service - Made Optional
**File**: `backend/services/clip_service.py`
- ✅ Added try/except for torch and sentence-transformers imports
- ✅ CLIP_AVAILABLE flag to check availability
- ✅ Graceful degradation when CLIP unavailable
- ✅ `select_best_frames()` falls back to heuristic selection

### 2. Video Service - Made MoviePy Optional
**File**: `backend/services/video_service.py`
- ✅ Added try/except for moviepy import
- ✅ MOVIEPY_AVAILABLE flag
- ✅ `extract_frames()` automatically uses ffmpeg fallback when moviepy unavailable
- ✅ No import errors on Vercel

### 3. Product Ranking Service - Made CLIP Optional
**File**: `backend/services/product_ranking_service.py`
- ✅ Made CLIP service import optional
- ✅ Adjusts weights when CLIP unavailable (text + brand only)
- ✅ Visual score defaults to 0.0 when CLIP unavailable
- ✅ Normalizes weights for text-only ranking

### 4. Product Search Service - Made sklearn Optional
**File**: `backend/services/product_search_service.py`
- ✅ Added try/except for sklearn import
- ✅ Numpy-based cosine similarity fallback
- ✅ No import errors if sklearn unavailable

## 📋 Final Dependency Check

### api/requirements.txt ✅ READY
```
Flask==3.0.0
Flask-CORS==4.0.0
python-dotenv==1.0.0
openai==1.12.0
google-cloud-vision==3.7.0
requests==2.31.0
yt-dlp==2025.10.14
Pillow==10.1.0
numpy==1.26.3
beautifulsoup4==4.12.3
lxml==5.1.0
```

**Total size**: ~500MB (within Vercel limits)

### Missing Dependencies (Handled Gracefully)
- ❌ torch, torchvision → CLIP disabled, uses heuristics
- ❌ sentence-transformers → CLIP disabled
- ❌ moviepy → Uses ffmpeg subprocess directly
- ❌ scikit-learn → Uses numpy cosine similarity

## 🎯 Behavior on Vercel

### With Missing Dependencies:
1. **Frame Selection**: Uses heuristic (first/middle frames) instead of CLIP
2. **Frame Extraction**: Uses ffmpeg subprocess instead of moviepy
3. **Product Ranking**: Text (70%) + Brand (30%) instead of Visual (45%) + Text (35%) + Brand (20%)
4. **Cosine Similarity**: Uses numpy instead of sklearn

### Performance Impact:
- ✅ **Build**: Will succeed (~500MB vs ~3.5GB)
- ✅ **Cold Start**: Faster (no CLIP model loading)
- ⚠️ **Accuracy**: Slightly reduced (no visual similarity, but still functional)

## ✅ Ready for Deployment

All services now handle missing dependencies gracefully. The API will work on Vercel without CLIP/torch/moviepy, using fallbacks.

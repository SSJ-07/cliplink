# Vercel Deployment Checklist

## 🔴 CRITICAL ISSUES FOUND

### Issue 1: CLIP Service Import (WILL FAIL)
- **File**: `api/analyze-reel.py` line 18
- **Problem**: Imports `clip_service` which requires `torch` + `sentence-transformers`
- **Impact**: Import will fail on Vercel (dependencies not in `api/requirements.txt`)
- **Fix**: Make CLIP optional or remove from API functions

### Issue 2: MoviePy Import (WILL FAIL)
- **File**: `backend/services/video_service.py` line 10
- **Problem**: Imports `moviepy` which requires ffmpeg binary
- **Impact**: Import will fail on Vercel (not in `api/requirements.txt`)
- **Fix**: Use ffmpeg fallback when moviepy unavailable

### Issue 3: Product Ranking Requires CLIP (WILL FAIL)
- **File**: `backend/services/product_ranking_service.py` line 8
- **Problem**: Requires CLIP service for visual similarity
- **Impact**: Will fail when CLIP unavailable
- **Fix**: Make CLIP optional, fallback to text-only ranking

## ✅ FIXES NEEDED

1. Make CLIP service optional (graceful degradation)
2. Make video_service use ffmpeg when moviepy unavailable
3. Make product_ranking_service work without CLIP
4. Update api/analyze-reel.py to handle missing CLIP gracefully

## 📋 DEPENDENCY CHECK

### api/requirements.txt ✅ CORRECT
- Flask, Flask-CORS, python-dotenv ✅
- openai, google-cloud-vision, requests ✅
- yt-dlp, Pillow ✅
- numpy ✅
- beautifulsoup4, lxml ✅
- **NO torch, moviepy, sentence-transformers** ✅

### backend/requirements.txt ⚠️ FOR LOCAL ONLY
- Has torch, moviepy, sentence-transformers
- **OK** - Only used for local development

## 🔧 CONFIGURATION CHECK

### vercel.json ✅ CORRECT
- Frontend build: `frontend/package.json` → `dist` ✅
- API functions: `api/*.py` ✅
- Routes configured correctly ✅
- Environment variables listed ✅

### frontend/package.json ✅ CORRECT
- Has `vercel-build` script ✅
- Dependencies look good ✅

## 🎯 ACTION ITEMS

1. ✅ Make CLIP service optional (fail gracefully)
2. ✅ Make video_service use ffmpeg fallback
3. ✅ Make product_ranking_service work without CLIP
4. ✅ Test imports don't fail on Vercel

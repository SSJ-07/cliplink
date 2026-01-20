# 🔍 Build Memory & Deployment Issues Report

## Section 1: 🔥 Critical Issues (Will Break Builds)

### 1.1 **CRITICAL SECURITY + BUILD FAILURE**
**File**: `cliplink-104c9-6b743f3b8596.json` (root directory)
- **Issue**: Google Cloud service account credentials with **PRIVATE KEY** committed to repository
- **Impact**: 
  - **SECURITY BREACH**: Private keys exposed in git history
  - Build failure: `.gitignore` has `*.json` but file is explicitly listed (line 211), suggesting it was committed before the ignore rule
- **Risk**: Anyone with repo access can impersonate your service account, incur charges, or access your GCP resources
- **Size**: ~2.5KB, but contains sensitive credentials

### 1.2 **MEMORY EXHAUSTION - PyTorch + Dependencies**
**Files**: 
- `api/requirements.txt` (lines 14-16)
- `backend/requirements.txt` (lines 14-16)
- `requirements.txt` (root, same content)

**Dependencies causing OOM**:
```
torch==2.8.0              # ~2.0GB+
torchvision==0.23.0       # ~500MB+
sentence-transformers==2.3.1  # ~200MB+ base + CLIP model ~600MB download
moviepy==1.0.3            # ~100MB+ + requires ffmpeg binary
scikit-learn==1.4.0       # ~50MB+
```

**Total estimated size**: ~3.5GB+ (exceeds Vercel's 1GB default build memory)

**Impact**: 
- Build will **FAIL** with "exceeded memory available" error
- Even if it succeeds, serverless function cold starts will be extremely slow
- Vercel Python functions have strict size limits (~50MB zipped)

### 1.3 **CLIP Model Loaded at Import Time**
**File**: `backend/services/clip_service.py` (lines 27, 33)
- **Issue**: CLIP model (`clip-ViT-B-32`) is loaded in `__init__()` which runs on import
- **Impact**: 
  - Importing `clip_service` immediately downloads and loads ~600MB model
  - Serverless function startup will OOM trying to load model
  - Model loads on EVERY cold start

### 1.4 **Vercel Configuration - Duplicate Builds**
**File**: `vercel.json`
- **Issue**: Python requirements installed for both `api/*.py` AND potentially `backend/` (if root `requirements.txt` is detected)
- **Impact**: Vercel might try to install dependencies twice, doubling memory usage

---

## Section 2: ⚠️ High-Risk Issues (Likely to Cause OOM or Slowness)

### 2.1 **Large Directories Potentially in Git**
**Directories that SHOULD be ignored but might be committed**:
- `backend/venv/` - Virtual environment (~500MB-2GB+)
- `frontend/node_modules/` - Node dependencies (~200-500MB)
- `old-frontend/node_modules/` - Old dependencies (~200-500MB)
- `old-frontend/dist/` - Build artifacts (size varies)

**Check needed**: Run `git ls-files | grep -E "(venv|node_modules|dist)"` to verify these aren't tracked

### 2.2 **Heavy Dependencies in API Requirements**
**File**: `api/requirements.txt`
- **Issue**: Contains ALL backend dependencies including PyTorch, even though Vercel serverless functions may not need all of them
- **Impact**: 
  - Unnecessary memory usage during build
  - Slower cold starts
  - Larger function package size

### 2.3 **MoviePy Requires FFmpeg Binary**
**File**: `backend/services/video_service.py`, `api/requirements.txt`
- **Issue**: `moviepy==1.0.3` requires `ffmpeg` binary, which Vercel serverless functions may not have
- **Impact**: 
  - Build might succeed but runtime will fail when trying to extract frames
  - You already have `ffmpeg` fallback in code, but `moviepy` still gets installed

### 2.4 **Redundant Requirements Files**
**Files**: 
- `requirements.txt` (root)
- `backend/requirements.txt`
- `api/requirements.txt`

**Issue**: All three have identical content, but Vercel might detect root `requirements.txt` and try to install it separately, causing conflicts or duplicate installs

---

## Section 3: 🧹 Cleanup Recommendations (Safe Improvements)

### 3.1 **.gitignore Inconsistencies**
**File**: `.gitignore` (lines 210-211)
- Line 210: `*.json` (should ignore all JSON)
- Line 211: `cliplink-104c9-6b743f3b8596.json` (redundant if line 210 works, but suggests file was committed before)
- **Issue**: Explicit listing suggests the file might already be in git history
- **Action**: Remove line 211 if `*.json` works, but verify file isn't tracked first

### 3.2 **Missing .gitignore Patterns**
**Missing patterns**:
- `.vercel/` - Vercel build cache
- `.cache/` - Build caches
- `dist/` - Should be more specific (only root level?)
- `*.log` - Log files (already in .gitignore for Python but not explicitly)

### 3.3 **Old Frontend Directory**
**Directory**: `old-frontend/`
- **Issue**: Entire old frontend with `node_modules/` and `dist/` in repo
- **Impact**: Unnecessary repository size (even if ignored, might be in history)
- **Recommendation**: Remove if no longer needed, or ensure fully ignored

### 3.4 **Vite Config Optimization**
**File**: `frontend/vite.config.ts`
- **Issue**: Alias `'@'` resolves to `__dirname` (current directory) instead of `'./src'`
- **Impact**: Potential import resolution issues, though might work by accident
- **Recommendation**: Should be `path.resolve(__dirname, './src')` for clarity

### 3.5 **Unused Dependencies**
**Potential candidates** (verify before removing):
- `scikit-learn` - Only used for `cosine_similarity`, but `numpy` has equivalent functions
- `lxml` - Only needed if parsing complex HTML, `beautifulsoup4` can use built-in parser

---

## Section 4: ✅ Exact Commands to Fix Each Issue

### Fix 1: Remove Credentials from Git History
```bash
# Step 1: Verify file is tracked
git ls-files | grep cliplink-104c9

# Step 2: Remove from git (but keep local copy temporarily)
git rm --cached cliplink-104c9-6b743f3b8596.json

# Step 3: Add to .gitignore (already there, but ensure it's working)
# Verify .gitignore line 210 has: *.json

# Step 4: Commit the removal
git commit -m "security: remove credentials file from git"

# Step 5: **CRITICAL** - Rotate the credentials in Google Cloud Console
# Go to IAM & Admin > Service Accounts > cliplink-vision
# Delete the old key and create a new one
# Update environment variable in Vercel with new credentials (base64 encoded)

# Step 6: Remove file from local filesystem (after rotating credentials)
rm cliplink-104c9-6b743f3b8596.json
```

### Fix 2: Remove Heavy Dependencies from API Requirements
```bash
# Create minimal api/requirements.txt for Vercel serverless functions
# Edit api/requirements.txt and remove:
# - torch==2.8.0
# - torchvision==0.23.0
# - sentence-transformers==2.3.1 (CLIP model)
# - moviepy==1.0.3 (use ffmpeg fallback only)

# Keep only:
# Flask, Flask-CORS, openai, requests, python-dotenv, 
# google-cloud-vision, numpy, beautifulsoup4
```

### Fix 3: Make CLIP Service Lazy-Load Only When Needed
```bash
# Edit backend/services/clip_service.py
# Change __init__ to NOT call _initialize_model()
# Only load model when first method is called
# This prevents model loading on import for serverless functions
```

### Fix 4: Verify Large Directories Are Ignored
```bash
# Check what's actually tracked in git
git ls-files | grep -E "(venv|node_modules|dist)" | head -20

# If any found, remove them:
git rm -r --cached backend/venv/ 2>/dev/null
git rm -r --cached frontend/node_modules/ 2>/dev/null
git rm -r --cached old-frontend/node_modules/ 2>/dev/null
git rm -r --cached old-frontend/dist/ 2>/dev/null

# Commit changes
git commit -m "chore: remove ignored directories from git"
```

### Fix 5: Remove Redundant Root Requirements.txt
```bash
# Option A: Delete root requirements.txt (recommended if only using api/ and backend/)
rm requirements.txt

# Option B: Keep it but ensure Vercel uses api/requirements.txt explicitly
# (Already handled in vercel.json builds config)
```

### Fix 6: Update .gitignore for Vercel
```bash
# Add these patterns to .gitignore (if not already present):
echo "" >> .gitignore
echo "# Vercel" >> .gitignore
echo ".vercel/" >> .gitignore
echo ".vercel/output/" >> .gitignore
```

### Fix 7: Clean Up Old Frontend (Optional)
```bash
# If old-frontend is no longer needed:
rm -rf old-frontend/

# OR ensure it's fully ignored:
# Already in .gitignore line 208: old-frontend/
```

---

## Section 5: 📦 Final Recommended .gitignore

```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# But DO track frontend lib folder
!frontend/lib/

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
# .python-version

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
.idea/

# Abstra
.abstra/

# Visual Studio Code
.vscode/

# Ruff stuff:
.ruff_cache/

# PyPI configuration file
.pypirc

# Cursor
.cursorignore
.cursorindexingignore

# Visual product search app (reference implementation)
visual-product-search-app-main/

# Old frontend (renamed from frontend)
old-frontend/

# Secrets - CRITICAL: Never commit credentials
*.json
!package.json
!package-lock.json
!tsconfig.json
!tsconfig.*.json
!vite.config.ts  # Actually a TS file, not JSON
!vercel.json  # Deployment config (no secrets)

# Node modules
node_modules/
frontend/node_modules/
old-frontend/node_modules/

# Build artifacts
dist/
build/
.next/
out/

# Vercel
.vercel/
.vercel/output/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*
```

---

## 🎯 Priority Action Plan

**IMMEDIATE (Do Now)**:
1. ✅ **Remove credentials from git and rotate keys** (Fix 1)
2. ✅ **Remove PyTorch from `api/requirements.txt`** (Fix 2)
3. ✅ **Make CLIP service lazy-load** (Fix 3)

**HIGH PRIORITY (Before Next Deploy)**:
4. ✅ **Verify large directories are ignored** (Fix 4)
5. ✅ **Update .gitignore** (Fix 6)

**MEDIUM PRIORITY (Cleanup)**:
6. ✅ **Remove redundant requirements.txt** (Fix 5)
7. ✅ **Fix Vite config alias** (if needed)

---

## 📊 Expected Results After Fixes

- **Build memory**: Reduced from ~3.5GB to ~500MB
- **Build time**: Reduced from timeout to ~2-5 minutes
- **Function size**: Reduced from >50MB to ~20-30MB
- **Cold start**: Reduced from timeout to ~5-10 seconds (without CLIP), or make CLIP optional/offloaded

---

## ⚠️ Important Notes

1. **CLIP Model**: After removing from `api/requirements.txt`, your serverless functions won't have CLIP. You have two options:
   - **Option A**: Disable CLIP in production (make it optional via env var)
   - **Option B**: Offload CLIP to a separate service (Railway, AWS Lambda with more memory, etc.)

2. **Credentials Rotation**: **CRITICAL** - Even after removing from git, the old key is in git history. You MUST rotate the Google Cloud service account key.

3. **Testing**: After making changes, test locally first, then deploy to Vercel staging/preview before production.

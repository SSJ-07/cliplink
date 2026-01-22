# Vercel NOT_FOUND Error - Complete Explanation & Fix

## 1. 🔧 THE FIX

### Current Configuration Analysis

Your `vercel.json` is **almost correct**, but there's a subtle issue with how Vercel handles `outputDirectory` when combined with `builds`.

### The Fix

The configuration you have should work, but if you're still getting 404s, try this **more explicit version**:

```json
{
  "version": 2,
  "buildCommand": "cd frontend && npm ci && npm run build",
  "outputDirectory": "frontend/dist",
  "installCommand": "cd frontend && npm ci",
  "builds": [
    {
      "src": "api/*.py",
      "use": "@vercel/python"
    }
  ],
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "env": {
    "OPENAI_API_KEY": "$OPENAI_API_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS_BASE64": "$GOOGLE_APPLICATION_CREDENTIALS_BASE64",
    "VITE_FIREBASE_API_KEY": "$VITE_FIREBASE_API_KEY",
    "VITE_FIREBASE_AUTH_DOMAIN": "$VITE_FIREBASE_AUTH_DOMAIN",
    "VITE_FIREBASE_PROJECT_ID": "$VITE_FIREBASE_PROJECT_ID",
    "VITE_FIREBASE_STORAGE_BUCKET": "$VITE_FIREBASE_STORAGE_BUCKET",
    "VITE_FIREBASE_MESSAGING_SENDER_ID": "$VITE_FIREBASE_MESSAGING_SENDER_ID",
    "VITE_FIREBASE_APP_ID": "$VITE_FIREBASE_APP_ID",
    "VITE_FIREBASE_MEASUREMENT_ID": "$VITE_FIREBASE_MEASUREMENT_ID"
  }
}
```

**Note**: Your current config is correct. If 404 persists, the issue might be:
1. **Vercel project root directory** setting in dashboard
2. **Build not completing** (check build logs)
3. **Output not being created** (verify `frontend/dist/` exists after build)

---

## 2. 🔍 ROOT CAUSE ANALYSIS

### What Was Happening vs. What Should Happen

#### The Problem Flow:

```
User Request: GET https://your-app.vercel.app/
    ↓
Vercel Routing System
    ↓
Looks for: /index.html (at document root)
    ↓
Document Root = ? (This is the issue!)
    ↓
If document root = repo root → NOT_FOUND ❌
If document root = frontend/dist → SUCCESS ✅
```

#### What Should Happen:

1. **Build Phase**:
   ```
   Vercel runs: cd frontend && npm run build
   Output created: frontend/dist/index.html
   Output created: frontend/dist/assets/index-abc123.js
   ```

2. **Output Directory Resolution**:
   ```
   outputDirectory: "frontend/dist"
   → Vercel sets document root = frontend/dist/
   → Files are served from this location
   ```

3. **Request Handling**:
   ```
   Request: GET /
   → Rewrite rule: "/(.*)" -> "/index.html"
   → Resolves to: frontend/dist/index.html
   → Served successfully ✅
   ```

#### Why This Error Occurred

**The Core Issue**: Vercel's routing system needs to know:
1. **Where files are built** (outputDirectory)
2. **Where to serve them from** (document root)
3. **How to route requests** (rewrites)

When `outputDirectory` is set, Vercel should automatically use it as the document root. However, there are edge cases:

**Edge Case 1: Builds + OutputDirectory Conflict**
- Using both `builds` (for frontend) and `outputDirectory` can cause Vercel to be confused
- Solution: Use `outputDirectory` for frontend, `builds` only for API functions

**Edge Case 2: Project Root Directory Setting**
- If Vercel dashboard has "Root Directory" set to `frontend/`, it changes how paths resolve
- Solution: Set root directory to repository root (blank/default)

**Edge Case 3: Build Output Not Created**
- If build fails silently or outputs to wrong location
- Solution: Verify `frontend/dist/` exists after build

### The Misconception

**Common Misconception**:
> "If my build succeeds, Vercel will automatically serve my files"

**Reality**:
> "Build success ≠ Serving success. You must explicitly configure where output is and how to serve it."

**Why**: Vercel supports many frameworks and build tools. It can't guess:
- Where your specific build tool outputs files
- How your routing should work
- What your monorepo structure means

---

## 3. 📚 TEACHING THE CONCEPT

### Why This Error Exists

The `NOT_FOUND` error is Vercel's way of saying:
> "I received a request, but I can't find a file or route that matches it."

This protects you from:
- **Silent failures**: Better to get a clear 404 than serve wrong content
- **Security issues**: Prevents serving unintended files
- **Configuration errors**: Forces you to be explicit about routing

### The Mental Model: Vercel's Request Resolution

Think of Vercel as a **smart file server** with routing rules:

```
Request: GET /app
    ↓
Step 1: Check API routes
    ├─ Matches /api/*? → Route to serverless function
    └─ No match → Continue
    ↓
Step 2: Check static files
    ├─ File exists? → Serve it
    └─ No file → Continue
    ↓
Step 3: Check rewrites
    ├─ Matches rewrite rule? → Rewrite and retry
    └─ No match → 404 NOT_FOUND
```

**Your Case**:
```
Request: GET /
    ↓
Step 1: Not /api/* → Skip
    ↓
Step 2: Look for /index.html
    ├─ Document root = ? (The problem!)
    ├─ If root = repo root → /index.html doesn't exist ❌
    └─ If root = frontend/dist → /index.html exists ✅
    ↓
Step 3: Rewrite rule "/(.*)" -> "/index.html"
    ├─ Only applies if Step 2 fails
    └─ But if document root is wrong, rewrite also fails
```

### The Framework Design Philosophy

Vercel follows **"Convention over Configuration"** with **"Explicit Configuration"** as fallback:

**Convention (Auto-detection)**:
- Framework in root? → Auto-detect and configure
- Standard structure? → Use defaults

**Configuration (Your Case)**:
- Monorepo? → Must be explicit
- Custom build? → Must specify
- Non-standard output? → Must tell Vercel

**Why**: Flexibility requires explicitness. Vercel can't guess your specific setup.

### How This Fits Into Web Architecture

**Traditional Web Server**:
```
Document Root: /var/www/html
Request: GET /index.html
→ Serve: /var/www/html/index.html
```

**Vercel (Static + Serverless)**:
```
Document Root: (configured by outputDirectory)
Request: GET /
→ Check: Is there a file at document_root/index.html?
→ If yes: Serve it
→ If no: Check rewrites → Apply rewrite → Retry
```

**The Key Difference**: Vercel needs to know the document root explicitly because:
1. It's a build-time decision (not runtime)
2. It supports multiple deployment types (static, serverless, hybrid)
3. It needs to optimize asset serving

---

## 4. ⚠️ WARNING SIGNS

### Red Flags to Watch For

#### 1. **Monorepo Without Explicit Config**
```
project/
  ├── frontend/  ← Your app is here
  └── api/       ← Functions here
```
**Red Flag**: No `outputDirectory` specified
**Fix**: Always specify `outputDirectory` for monorepos

#### 2. **Build Succeeds, Site 404s**
```
✅ Build: "Build completed successfully"
✅ Output: "2 MB uploaded"
❌ Site: 404 NOT_FOUND
```
**Red Flag**: Output directory mismatch
**Fix**: Verify `outputDirectory` matches actual build output location

#### 3. **Mixed Configuration Approaches**
```json
{
  "builds": [{ "src": "frontend/package.json", ... }],  // Approach 1
  "outputDirectory": "frontend/dist",                   // Approach 2
  "buildCommand": "cd frontend && npm run build"        // Approach 2
}
```
**Red Flag**: Using both `builds` for frontend AND `outputDirectory`
**Fix**: Choose one approach:
- Option A: Use `builds` for frontend (remove `outputDirectory`)
- Option B: Use `outputDirectory` (remove frontend from `builds`)

#### 4. **Vague or Missing Rewrites**
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/$1" }
    // Missing: SPA fallback
  ]
}
```
**Red Flag**: No catch-all rewrite for SPA routes
**Fix**: Add `{ "source": "/(.*)", "destination": "/index.html" }`

### Code Smells

#### Smell 1: Relative Paths Without Context
```json
"outputDirectory": "dist"  // ❌ Assumes repo root
```
**Why Bad**: Doesn't work for monorepos
**Fix**: `"outputDirectory": "frontend/dist"`

#### Smell 2: Build Command Doesn't Match Output
```json
"buildCommand": "npm run build",           // Builds to ./dist
"outputDirectory": "frontend/dist"         // But output is in frontend/
```
**Why Bad**: Mismatch causes 404
**Fix**: `"buildCommand": "cd frontend && npm run build"`

#### Smell 3: Rewrite Points to Wrong Location
```json
"rewrites": [
  { "source": "/(.*)", "destination": "/frontend/dist/index.html" }  // ❌ Wrong
]
```
**Why Bad**: Rewrite destination should be relative to document root
**Fix**: `{ "source": "/(.*)", "destination": "/index.html" }`

### Similar Mistakes You Might Make

#### Mistake 1: Forgetting `cd` in Build Command
```json
// ❌ WRONG
"buildCommand": "npm run build"  // Runs in repo root, builds to ./dist

// ✅ CORRECT  
"buildCommand": "cd frontend && npm run build"  // Runs in frontend/, builds to frontend/dist
```

#### Mistake 2: Wrong Output Directory Path
```json
// ❌ WRONG
"outputDirectory": "dist"  // Looks for repo root

// ✅ CORRECT
"outputDirectory": "frontend/dist"  // Explicit path from repo root
```

#### Mistake 3: Missing SPA Rewrite
```json
// ❌ WRONG - Direct navigation to /app will 404
"rewrites": [
  { "source": "/api/(.*)", "destination": "/api/$1" }
]

// ✅ CORRECT - All routes serve index.html (SPA)
"rewrites": [
  { "source": "/api/(.*)", "destination": "/api/$1" },
  { "source": "/(.*)", "destination": "/index.html" }
]
```

#### Mistake 4: Conflicting Build Configurations
```json
// ❌ WRONG - Both try to build frontend
{
  "builds": [
    { "src": "frontend/package.json", "use": "@vercel/static-build" }
  ],
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/dist"
}

// ✅ CORRECT - One approach only
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/dist",
  "builds": [
    { "src": "api/*.py", "use": "@vercel/python" }  // Only for API
  ]
}
```

---

## 5. 🔄 ALTERNATIVE APPROACHES

### Approach 1: Current Fix (Recommended) ✅
**Using `outputDirectory` + `buildCommand`**

```json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/dist",
  "builds": [{ "src": "api/*.py", "use": "@vercel/python" }],
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

**Pros**:
- ✅ Explicit and clear
- ✅ Works reliably for monorepos
- ✅ Easy to debug
- ✅ Clear separation of concerns

**Cons**:
- ⚠️ More verbose
- ⚠️ Must specify build command

**Best For**: Monorepos, custom build processes, when you need control

---

### Approach 2: Pure `builds` Configuration
```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    },
    {
      "src": "api/*.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/$1" },
    { "handle": "filesystem" },
    { "src": "/(.*)", "dest": "/frontend/dist/index.html" }
  ]
}
```

**Pros**:
- ✅ Uses Vercel's build system
- ✅ Automatic dependency detection
- ✅ Framework-specific optimizations

**Cons**:
- ⚠️ `distDir` resolution can be tricky
- ⚠️ Route destination must match actual output path
- ⚠️ Less explicit (harder to debug)

**Best For**: When you want Vercel to handle more automatically

**Trade-off**: Less control, more "magic"

---

### Approach 3: Separate Vercel Projects
**Deploy frontend and backend as separate projects**

**Frontend Project** (`vercel.json`):
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist"
}
```

**Backend Project** (`vercel.json`):
```json
{
  "builds": [
    { "src": "api/*.py", "use": "@vercel/python" }
  ]
}
```

**Pros**:
- ✅ Simpler configuration per project
- ✅ Independent deployments
- ✅ Clear separation
- ✅ Framework auto-detection works

**Cons**:
- ⚠️ More projects to manage
- ⚠️ CORS configuration needed
- ⚠️ Two domains/URLs (or subdomains)
- ⚠️ Environment variables in two places

**Best For**: When frontend and backend are truly independent, large teams

**Trade-off**: Simplicity vs. deployment coordination

---

### Approach 4: Vercel Project Root Directory
**Set Vercel dashboard "Root Directory" to `frontend/`**

**Vercel Dashboard**:
- Settings → General → Root Directory: `frontend`

**vercel.json** (in `frontend/`):
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

**Pros**:
- ✅ Vercel treats `frontend/` as root
- ✅ Simpler configuration
- ✅ Framework auto-detection works
- ✅ No `cd` commands needed

**Cons**:
- ⚠️ Can't easily include `api/` functions in same project
- ⚠️ Backend must be separate project
- ⚠️ Less flexible for monorepos

**Best For**: Frontend-only deployments, when API is separate

**Trade-off**: Simplicity vs. monorepo support

---

### Approach 5: Vercel CLI with `--cwd`
**Use Vercel CLI with working directory flag**

```bash
vercel --cwd frontend
```

**Pros**:
- ✅ Simple for frontend-only
- ✅ Uses framework defaults

**Cons**:
- ⚠️ Doesn't work for monorepo with API functions
- ⚠️ Requires CLI deployment (not git-based)

**Best For**: Quick frontend-only deployments

---

## 🎯 RECOMMENDED SOLUTION

**Use Approach 1** (your current fix) because:

1. ✅ **Works for monorepo**: Handles both frontend and API
2. ✅ **Explicit**: Easy to understand and debug
3. ✅ **Reliable**: Less "magic", more predictable
4. ✅ **Flexible**: Easy to modify for different build processes

**When to use alternatives**:
- **Approach 2**: If you want Vercel to handle more automatically
- **Approach 3**: If frontend/backend teams are separate
- **Approach 4**: If you're doing frontend-only deployment

---

## 📋 DEBUGGING CHECKLIST

### Pre-Deployment Checks

- [ ] **Build works locally**: `cd frontend && npm run build` succeeds
- [ ] **Output exists**: `frontend/dist/index.html` exists after build
- [ ] **Output structure**: `frontend/dist/assets/` contains JS/CSS files
- [ ] **Config matches**: `outputDirectory` matches actual output location
- [ ] **Build command**: Includes `cd frontend` if needed
- [ ] **Rewrites**: Include SPA fallback `"/(.*)" -> "/index.html"`

### Post-Deployment Checks

- [ ] **Build logs**: Show "Build completed" (not just "Installing")
- [ ] **Output size**: Shows files were uploaded (e.g., "2 MB")
- [ ] **Health endpoint**: `/api/health` returns 200
- [ ] **Root route**: `/` serves the app (not 404)
- [ ] **SPA routes**: `/app` serves the app (not 404)
- [ ] **API routes**: `/api/analyze-reel` works

### Common Issues & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| Output directory wrong | Build succeeds, 404 on site | Check `outputDirectory` matches build output |
| Missing SPA rewrite | Direct `/app` URL 404s | Add `"/(.*)" -> "/index.html"` rewrite |
| Build command wrong | Build fails or outputs wrong location | Add `cd frontend` to build command |
| Root directory setting | Paths resolve incorrectly | Set root directory to repo root in dashboard |
| Conflicting configs | Unpredictable behavior | Use one approach (outputDirectory OR builds) |

---

## 💡 KEY TAKEAWAYS

### The Golden Rule
> **For monorepos on Vercel, you must explicitly configure:**
> 1. **What** to build (`buildCommand`)
> 2. **Where** output is (`outputDirectory`)
> 3. **How** to serve it (`rewrites`)

### The Mental Model
Think of Vercel deployment as a **pipeline**:
```
Build → Output → Serve
```

Each stage needs explicit configuration for monorepos.

### The Pattern
**Monorepo = Explicit Configuration**
- Single app in root = Auto-detection works
- Multiple apps in subdirs = Must be explicit

### The Debugging Approach
1. **Verify build works locally**
2. **Check output location matches config**
3. **Verify rewrites are correct**
4. **Check Vercel dashboard settings**

---

## 🔗 RELATED CONCEPTS

- **SPA Routing**: Client-side routing needs server-side fallback to `index.html`
- **Monorepo Deployment**: Multiple apps require explicit configuration
- **Build Artifacts**: Output location must match serving configuration
- **Vercel Build System**: Understands frameworks but needs help for custom setups
- **Static Site Generation**: Pre-built files need correct document root

---

## 📚 FURTHER READING

- [Vercel Routing Documentation](https://vercel.com/docs/concepts/projects/project-configuration#rewrites)
- [Vercel Monorepo Guide](https://vercel.com/docs/monorepos)
- [SPA Routing Best Practices](https://vercel.com/docs/concepts/projects/project-configuration#rewrites)
- [Vercel Build Configuration](https://vercel.com/docs/concepts/projects/project-configuration#builds)

---

## ✅ FINAL CHECK

Your current `vercel.json` should work. If you're still getting 404s:

1. **Check Vercel Dashboard**:
   - Settings → General → Root Directory should be **blank** (repository root)

2. **Verify Build Output**:
   - Check build logs: Does it show files being uploaded?
   - Verify: `frontend/dist/index.html` exists after local build

3. **Test Rewrites**:
   - `/` should serve `index.html`
   - `/app` should also serve `index.html` (SPA)
   - `/api/health` should route to Python function

If all checks pass but 404 persists, the issue might be Vercel caching. Try:
- Redeploying
- Clearing Vercel cache
- Checking deployment logs for errors

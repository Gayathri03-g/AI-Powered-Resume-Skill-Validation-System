# 🎯 Skill Assessment System

Industry-grade backend for skill-based candidate evaluation.

## 🔒 System Flow
1. **Resume Upload** → Extract text from PDF/DOCX
2. **Skill Analysis** → Gemini-based skill extraction
3. **Quiz Round** → Dynamic question generation and evaluation
4. **Coding Round** → Sandboxed code execution with test cases
5. **Final Report** → Learning-focused feedback generation

## 📁 Project Structure
```
ttt/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # API endpoint handlers
│   │       └── router.py       # Route aggregation
│   ├── core/
│   │   └── config.py          # Settings & environment
│   └── main.py                # FastAPI app factory
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
└── run.py                     # Server launcher
```

## 🚀 Quick Start (CHUNK 1.1)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and update values:
```bash
GEMINI_API_KEY=your-actual-api-key
```

### 3. Run Server
```bash
python run.py
```

### 4. Verify Health
Open browser: `http://localhost:19440/health`

Expected response:
```json
{
  "status": "healthy",
  "app_name": "Skill Assessment System",
  "version": "1.0.0"
}
```

## 🔗 Connection Verification

### Frontend Access
- **Main App:** http://localhost:19440
- **Connection Test:** http://localhost:19440/test-connection.html

### API Endpoints
- **Health Check:** http://localhost:19440/api/v1/health
- **Connection Test:** http://localhost:19440/api/v1/connection-test
- **CORS Test:** http://localhost:19440/api/v1/test-cors
- **Ping:** http://localhost:19440/api/v1/ping

### Visual Confirmation
✅ Connection badge appears in top-right corner  
✅ Shows "Backend Connected" with pulsing cyan dot  
✅ Click badge to open detailed connection test  

### Keyboard Shortcuts
- `Ctrl/Cmd + K` - Open connection test page
- `Escape` - Close modals

**See [CONNECTION_STATUS.md](CONNECTION_STATUS.md) for complete connection details.**


## 📚 API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧱 Build Progress
- ✅ **CHUNK 1.1** - Project Skeleton & Config
- ⏳ **CHUNK 1.2** - Resume Upload API
- ⏳ **CHUNK 1.3** - Resume Text Extraction
- ⏳ ... (more chunks to come)

---
Built with zero ambiguity, one chunk at a time.

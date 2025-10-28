# Quick Start Guide

Get your TED Talk Analyzer up and running in 5 minutes!

## Prerequisites Check

```bash
# Check Node.js (need 18+)
node --version

# Check Python (need 3.8+)
python3 --version

# Check FFmpeg
ffmpeg -version
```

If FFmpeg is missing:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

## Step 1: Start Frontend (2 minutes)

```bash
cd frontend

# Already installed? Skip this
# npm install

# Start dev server
npm run dev
```

✅ Frontend running at http://localhost:3000

## Step 2: Start Backend (3 minutes)

Open a **new terminal**:

```bash
cd backend

# Create virtual environment (first time only)
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies (first time only - takes 2-3 minutes)
pip install -r requirements.txt

# Set up API keys (optional for testing - backend has fallbacks)
cp .env.example .env
# Edit .env if you have OpenAI/Anthropic keys

# Start server
python main.py
```

✅ Backend running at http://localhost:8000

## Step 3: Test It!

1. Open browser: http://localhost:3000
2. Upload a short video (test with < 2 minutes for quick results)
3. Click "Analyze Video"
4. View the interactive dashboard!

## Troubleshooting

### Frontend won't start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend import errors
```bash
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### "ffmpeg not found"
Install FFmpeg (see prerequisites above)

### Out of memory during analysis
- Use shorter videos (< 5 minutes)
- Or edit `backend/processing/audio_processor.py` line 16, change model to "tiny"

## Next Steps

- Check out `/frontend/app/page.tsx` for upload UI
- Check out `/frontend/app/analysis/[id]/page.tsx` for dashboard
- Check out `/backend/main.py` for API endpoints
- Read full docs in `README.md`

## API Testing

```bash
# Health check
curl http://localhost:8000/

# Upload video (replace path)
curl -X POST http://localhost:8000/api/analyze \
  -F "video=@/path/to/your/video.mp4"
```

## Common Issues

**Port 3000 already in use:**
```bash
# Kill existing process
lsof -ti:3000 | xargs kill -9
# Or use different port
npm run dev -- -p 3001
```

**Port 8000 already in use:**
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9
# Or edit main.py to use different port
```

**Whisper model download:**
First run downloads ~140MB model automatically. Wait for it to complete.

## Development Mode

Both servers support hot reload:
- Frontend: Auto-reloads on file changes
- Backend: Auto-reloads on Python file changes

Happy analyzing! 🎤✨

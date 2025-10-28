# TED Talk Analyzer - Backend

Python FastAPI backend for analyzing TED talks using computer vision, speech recognition, and LLM analysis.

## Features

- **Emotion Analysis**: Facial expression tracking using OpenCV and MediaPipe
- **Gesture Recognition**: Body language and hand gesture analysis
- **Speech Transcription**: Audio-to-text using OpenAI Whisper
- **Content Analysis**: LLM-powered insights using GPT-4 or Claude
- **Multimodal Correlation**: Synchronized analysis across all modalities

## Tech Stack

- **FastAPI**: Modern, fast web framework
- **OpenCV**: Computer vision for video processing
- **MediaPipe**: Pose and face detection
- **Whisper**: Speech-to-text transcription
- **OpenAI/Anthropic**: LLM content analysis
- **FFmpeg**: Audio extraction

## Setup

### 1. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install FFmpeg

FFmpeg is required for audio extraction:

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

### 3. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
# You need either OpenAI or Anthropic API key
```

### 4. Run the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /api/analyze
Upload and analyze a TED talk video

**Request:**
- Content-Type: multipart/form-data
- Body: video file

**Response:**
```json
{
  "analysis_id": "analysis_20241027_123456",
  "status": "completed",
  "data": {
    "emotions": [...],
    "gestures": [...],
    "transcript": [...],
    "llm_insights": {...},
    "summary": {...}
  }
}
```

### GET /api/analysis/{analysis_id}
Retrieve existing analysis results

## Directory Structure

```
backend/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── processing/            # Processing modules
│   ├── video_processor.py # Emotion & gesture analysis
│   ├── audio_processor.py # Transcription
│   └── llm_analyzer.py    # Content analysis
├── uploads/              # Uploaded videos (auto-created)
└── results/              # Analysis results (auto-created)
```

## Development

### Testing the API

```bash
# Test health check
curl http://localhost:8000/

# Upload video for analysis
curl -X POST http://localhost:8000/api/analyze \
  -F "video=@path/to/tedtalk.mp4"
```

### Interactive API Docs

Visit `http://localhost:8000/docs` for Swagger UI documentation

## Performance Notes

- First run will download Whisper model (~140MB for 'base' model)
- GPU acceleration recommended for faster processing
- Processing time: ~2-5 minutes for a 10-minute video (CPU)
- Reduce Whisper model size for faster processing (use 'tiny' or 'small')

## Troubleshooting

### Import Error: No module named 'cv2'
```bash
pip install opencv-python opencv-contrib-python
```

### FFmpeg not found
Ensure FFmpeg is installed and in your PATH

### Out of Memory
- Use smaller Whisper model ('tiny' or 'base')
- Process shorter videos
- Reduce sampling rate in video_processor.py

## Future Enhancements

- [ ] Real-time processing with WebSocket
- [ ] Support for multiple languages
- [ ] Enhanced emotion recognition with deep learning
- [ ] Voice tone analysis with librosa
- [ ] Audience reaction detection
- [ ] Export reports to PDF

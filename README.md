# GrowQR - AI-Powered Video Analysis

A comprehensive AI-powered platform for analyzing presentation videos using computer vision, speech recognition, and large language models.

## Overview

This application analyzes presentation videos to extract multiple layers of insight:

- **Visual Analysis**: Speaker emotions, facial expressions, gestures, and body language
- **Audio Analysis**: Speech transcription with timestamps and voice tone analysis
- **Content Analysis**: AI-powered insights on themes, rhetoric, persuasion techniques
- **Multimodal Correlation**: Synchronized analysis showing how visual, audio, and content elements work together

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
│  - Video Upload Interface                                    │
│  - Real-time Analysis Dashboard                             │
│  - Interactive Timeline Visualization                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ REST API
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  - Video Processing (OpenCV + MediaPipe)                     │
│  - Audio Transcription (Whisper)                             │
│  - LLM Analysis (GPT-4/Claude)                               │
└──────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Frontend
- **Next.js 16** with App Router
- **React 19** with TypeScript
- **Tailwind CSS** for styling
- **Turbopack** for fast builds

### Backend
- **FastAPI** - Modern Python web framework
- **OpenCV** - Computer vision and video processing
- **MediaPipe** - Face and pose detection
- **Whisper** - Speech-to-text transcription
- **OpenAI/Anthropic** - LLM content analysis

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- FFmpeg
- GPU recommended (for faster processing)

### 1. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys

# Run server
python main.py
```

Backend API will be available at `http://localhost:8000`

## Features

### 1. Emotion Analysis 😀
- Real-time facial expression tracking
- Emotion timeline showing speaker's emotional journey
- Confidence scores for each emotion detection
- Visual markers for emotional peaks

### 2. Gesture Recognition 👐
- Body language analysis using pose estimation
- Hand movement tracking
- Stage presence metrics
- Key gesture highlights with timestamps

### 3. Speech Transcription 🎤
- Accurate speech-to-text with Whisper
- Word-level timestamps
- Interactive transcript viewer
- Sync with video playback

### 4. AI Content Insights 🧠
- Main topics and themes identification
- Rhetorical technique analysis
- Argument structure breakdown
- Persuasion effectiveness scoring
- Overall tone analysis

### 5. Interactive Dashboard 📊
- Synchronized timeline view
- Real-time emotion and gesture tracking
- Summary statistics
- Key moments identification
- Multimodal correlation insights

## Usage

1. **Upload Video**: Drag and drop or select a presentation video (MP4, MOV, AVI)
2. **Processing**: Backend analyzes video (2-5 minutes for 10-minute video)
3. **View Results**: Interactive dashboard with all analysis layers
4. **Explore Timeline**: Click transcript segments to jump to moments
5. **AI Summary**: View comprehensive AI-generated summary of the presentation
6. **Export**: Download analysis results (coming soon)

## Project Structure

```
growqr/
├── frontend/                # Next.js frontend
│   ├── app/
│   │   ├── page.tsx        # Upload page
│   │   ├── analysis/       # Analysis dashboard
│   │   └── api/            # API routes
│   ├── public/
│   └── package.json
├── backend/                 # Python backend
│   ├── main.py             # FastAPI app
│   ├── processing/         # Analysis modules
│   ├── requirements.txt
│   └── README.md
├── problem-statement.md     # Original requirements
└── README.md               # This file
```

## API Documentation

### Upload and Analyze
```bash
POST http://localhost:8000/api/analyze
Content-Type: multipart/form-data

{
  "video": <file>
}
```

### Get Analysis Results
```bash
GET http://localhost:8000/api/analysis/{analysis_id}
```

Interactive API docs available at `http://localhost:8000/docs`

## Development

### Running Tests
```bash
# Frontend
cd frontend
npm test

# Backend
cd backend
pytest
```

### Building for Production

```bash
# Frontend
cd frontend
npm run build
npm start

# Backend - Use production server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Performance Tips

- Use GPU for 5-10x faster processing
- Reduce Whisper model size ('tiny' or 'base') for faster transcription
- Sample video frames at lower rates for quicker emotion analysis
- Process shorter videos for testing (< 5 minutes)

## Future Enhancements

- [ ] Real-time streaming analysis
- [ ] Multi-language support
- [ ] Audience reaction detection
- [ ] Advanced voice tone analysis
- [ ] PDF report export
- [ ] Batch processing multiple videos
- [ ] Speaker comparison analytics
- [ ] Custom training for domain-specific talks

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- OpenAI Whisper for speech recognition
- Google MediaPipe for pose estimation
- OpenAI/Anthropic for LLM capabilities

## Support

For issues and questions:
- Check the documentation in `/frontend/README.md` and `/backend/README.md`
- Open an issue on GitHub
- Review the problem statement in `problem-statement.md`

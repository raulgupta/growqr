"""
TED Talk Analyzer - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path
import shutil
from datetime import datetime
import os
import asyncio
from typing import Dict, Optional
import json

from processing.video_processor import VideoProcessor
from processing.audio_processor import AudioProcessor
from processing.llm_analyzer import LLMAnalyzer

app = FastAPI(
    title="TED Talk Analyzer API",
    description="AI-powered analysis of TED talks using computer vision and NLP",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Initialize processors
video_processor = VideoProcessor()
audio_processor = AudioProcessor()
llm_analyzer = LLMAnalyzer()

# Progress tracking
progress_updates: Dict[str, list] = {}
analysis_results: Dict[str, Optional[dict]] = {}
analysis_errors: Dict[str, str] = {}

# Mount static files for video access
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


def add_progress(analysis_id: str, message: str):
    """Add a progress update for an analysis"""
    if analysis_id not in progress_updates:
        progress_updates[analysis_id] = []
    progress_updates[analysis_id].append(message)
    print(message)  # Also log to console


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "TED Talk Analyzer API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/api/progress/{analysis_id}")
async def stream_progress(analysis_id: str):
    """Stream progress updates via Server-Sent Events"""
    async def event_generator():
        last_sent_index = 0

        # Wait for analysis to start
        for _ in range(100):  # Wait up to 10 seconds
            if analysis_id in progress_updates:
                break
            await asyncio.sleep(0.1)

        # Stream progress updates
        while True:
            if analysis_id in progress_updates:
                messages = progress_updates[analysis_id]

                # Send any new messages
                while last_sent_index < len(messages):
                    message = messages[last_sent_index]
                    yield f"data: {json.dumps({'message': message, 'index': last_sent_index})}\n\n"
                    last_sent_index += 1

                # Check if analysis is complete
                if any("Analysis completed" in msg or "error" in msg.lower() for msg in messages):
                    yield f"data: {json.dumps({'message': 'DONE', 'index': last_sent_index})}\n\n"
                    break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def process_video_background(analysis_id: str, video_path: Path, video_filename: str):
    """Background task to process video"""
    try:
        add_progress(analysis_id, f"🎬 Processing video: {video_path.name}")

        # 1. Extract frames and analyze emotions/gestures
        add_progress(analysis_id, "😀 Analyzing emotions and gestures...")
        emotion_data = video_processor.analyze_emotions(str(video_path))
        add_progress(analysis_id, f"✅ Detected {len(emotion_data)} emotion samples")

        gesture_data = video_processor.analyze_gestures(str(video_path))
        add_progress(analysis_id, f"✅ Detected {len(gesture_data)} gestures")

        # 2. Extract and transcribe audio
        add_progress(analysis_id, "🎤 Extracting and transcribing audio...")
        audio_path = audio_processor.extract_audio(str(video_path))
        add_progress(analysis_id, "✅ Audio extracted successfully")

        transcript = audio_processor.transcribe(audio_path)
        add_progress(analysis_id, f"✅ Transcribed {len(transcript)} segments")

        # 3. LLM analysis of transcript
        add_progress(analysis_id, "🧠 Performing AI content analysis...")
        llm_insights = llm_analyzer.analyze_content(transcript)
        add_progress(analysis_id, "✅ AI analysis completed")

        # 3.5. Generate AI summary
        add_progress(analysis_id, "📝 Generating AI summary...")
        transcript_summary = llm_analyzer.generate_summary(transcript, emotion_data, gesture_data)
        llm_insights["transcript_summary"] = transcript_summary
        add_progress(analysis_id, "✅ AI summary generated")

        # 4. Correlate multimodal data
        add_progress(analysis_id, "🔗 Correlating multimodal data...")
        correlated_data = correlate_analysis(
            emotion_data,
            gesture_data,
            transcript,
            llm_insights
        )
        add_progress(analysis_id, "✅ Analysis completed successfully!")

        # Save results
        result_path = RESULTS_DIR / f"{analysis_id}.json"
        with result_path.open("w") as f:
            json.dump(correlated_data, f, indent=2)

        # Generate video URL path
        video_url = f"http://localhost:8000/uploads/{video_path.name}"

        # Store results
        analysis_results[analysis_id] = {
            "data": correlated_data,
            "video_path": video_url
        }

    except Exception as e:
        error_msg = f"❌ Error processing video: {str(e)}"
        add_progress(analysis_id, error_msg)
        analysis_errors[analysis_id] = str(e)
        print(error_msg)


@app.post("/api/analyze")
async def analyze_video(video: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Main endpoint to analyze uploaded TED talk video

    Args:
        video: Uploaded video file

    Returns:
        Analysis ID for tracking progress
    """
    try:
        # Validate file type
        if not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")

        # Generate unique ID for this analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_id = f"analysis_{timestamp}"

        # Initialize progress tracking
        add_progress(analysis_id, f"📹 Uploading video: {video.filename}")

        # Save uploaded video
        video_path = UPLOAD_DIR / f"{analysis_id}_{video.filename}"
        with video_path.open("wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        add_progress(analysis_id, f"✅ Video uploaded successfully")

        # Start background processing
        background_tasks.add_task(process_video_background, analysis_id, video_path, video.filename)

        # Return immediately with analysis ID
        return JSONResponse({
            "analysis_id": analysis_id,
            "status": "processing"
        })

    except Exception as e:
        print(f"Error processing video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/{analysis_id}")
async def get_results(analysis_id: str):
    """Get the results of a completed analysis"""
    if analysis_id in analysis_errors:
        raise HTTPException(status_code=500, detail=analysis_errors[analysis_id])

    if analysis_id not in analysis_results:
        return JSONResponse({"status": "processing"})

    result = analysis_results[analysis_id]
    return JSONResponse({
        "status": "completed",
        "data": result["data"],
        "video_path": result["video_path"]
    })


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Retrieve existing analysis results

    Args:
        analysis_id: Unique identifier for the analysis

    Returns:
        Stored analysis results
    """
    result_path = RESULTS_DIR / f"{analysis_id}.json"

    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Analysis not found")

    import json
    with result_path.open("r") as f:
        data = json.load(f)

    return JSONResponse(data)


def correlate_analysis(emotions, gestures, transcript, llm_insights):
    """
    Correlate all analysis streams with timestamps

    Args:
        emotions: List of emotion detections with timestamps
        gestures: List of gesture detections with timestamps
        transcript: Transcribed text with timestamps
        llm_insights: LLM-generated insights

    Returns:
        Integrated analysis data
    """
    return {
        "emotions": emotions,
        "gestures": gestures,
        "transcript": transcript,
        "llm_insights": llm_insights,
        "summary": {
            "total_duration": round(max([e["time"] for e in emotions])) if emotions else 0,
            "emotional_range": list(set([e["emotion"] for e in emotions])),
            "key_moments": identify_key_moments(emotions, gestures, transcript),
            "top_themes": llm_insights.get("main_topics", []),
        }
    }


def identify_key_moments(emotions, gestures, transcript):
    """
    Identify key moments based on multimodal signals

    Returns:
        List of key moments with timestamps and descriptions
    """
    key_moments = []

    # Find high-confidence emotion peaks
    for emotion in emotions:
        if emotion.get("confidence", 0) > 0.85:
            key_moments.append({
                "time": round(emotion["time"]),
                "description": f"Peak {emotion['emotion']} emotion detected",
                "type": "emotion"
            })

    # Add gesture highlights
    for gesture in gestures[:3]:  # Top 3 gestures
        key_moments.append({
            "time": round(gesture["time"]),
            "description": gesture["description"],
            "type": "gesture"
        })

    return sorted(key_moments, key=lambda x: x["time"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

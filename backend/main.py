"""
TED Talk Analyzer - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uvicorn
from pathlib import Path
import shutil
from datetime import datetime
import os
import asyncio
from typing import Dict, Optional
import json
from uuid import UUID

from processing.video_processor import VideoProcessor
from processing.audio_processor import AudioProcessor
from processing.llm_analyzer import LLMAnalyzer

# Database imports
from database import get_db, engine, Base
from database.models import VideoStatus, AnalysisStatus
import database.crud as crud

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


# Database initialization
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🗄️  Initializing database...")
    # Tables are already created via Alembic migrations
    # This is just for logging
    print("✅ Database ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down...")


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


def process_video_background(analysis_id: UUID, video_id: UUID, video_path: Path, video_filename: str):
    """Background task to process video"""
    db = next(get_db())

    try:
        add_progress(str(analysis_id), f"🎬 Processing video: {video_path.name}")

        # Update analysis status
        crud.update_analysis_status(db, analysis_id, AnalysisStatus.PROCESSING, progress=10)

        # 1. Extract frames and analyze emotions/gestures
        add_progress(str(analysis_id), "😀 Analyzing emotions and gestures...")
        emotion_data = video_processor.analyze_emotions(str(video_path))
        add_progress(str(analysis_id), f"✅ Detected {len(emotion_data)} emotion samples")

        crud.update_analysis_status(db, analysis_id, AnalysisStatus.PROCESSING, progress=30)

        gesture_data = video_processor.analyze_gestures(str(video_path))
        add_progress(str(analysis_id), f"✅ Detected {len(gesture_data)} gestures")

        crud.update_analysis_status(db, analysis_id, AnalysisStatus.PROCESSING, progress=40)

        # 2. Extract and transcribe audio
        add_progress(str(analysis_id), "🎤 Extracting and transcribing audio...")
        audio_path = audio_processor.extract_audio(str(video_path))
        add_progress(str(analysis_id), "✅ Audio extracted successfully")

        transcript = audio_processor.transcribe(audio_path)
        add_progress(str(analysis_id), f"✅ Transcribed {len(transcript)} segments")

        crud.update_analysis_status(db, analysis_id, AnalysisStatus.PROCESSING, progress=60)

        # 3. LLM analysis of transcript
        add_progress(str(analysis_id), "🧠 Performing AI content analysis...")
        llm_insights = llm_analyzer.analyze_content(transcript)
        add_progress(str(analysis_id), "✅ AI analysis completed")

        crud.update_analysis_status(db, analysis_id, AnalysisStatus.PROCESSING, progress=75)

        # 3.5. Generate AI summary
        add_progress(str(analysis_id), "📝 Generating AI summary...")
        transcript_summary = llm_analyzer.generate_summary(transcript, emotion_data, gesture_data)
        llm_insights["transcript_summary"] = transcript_summary
        add_progress(str(analysis_id), "✅ AI summary generated")

        crud.update_analysis_status(db, analysis_id, AnalysisStatus.PROCESSING, progress=85)

        # 4. Save to database
        add_progress(str(analysis_id), "💾 Saving results to database...")

        # Calculate total duration
        total_duration = max([e["time"] for e in emotion_data]) if emotion_data else 0
        crud.set_analysis_duration(db, analysis_id, total_duration)

        # Save emotions
        emotions_for_db = [
            {
                "timestamp": e["time"],
                "emotion": e["emotion"],
                "confidence": e["confidence"]
            }
            for e in emotion_data
        ]
        crud.create_emotions_bulk(db, analysis_id, emotions_for_db)

        # Save gestures
        gestures_for_db = [
            {
                "timestamp": g["time"],
                "type": g["type"],
                "description": g["description"],
                "confidence": g["confidence"]
            }
            for g in gesture_data
        ]
        crud.create_gestures_bulk(db, analysis_id, gestures_for_db)

        # Save transcript
        transcripts_for_db = [
            {
                "segment_index": idx,
                "start_time": t["time"],
                "end_time": t.get("end_time", t["time"] + 5),
                "text": t["text"],
                "confidence": t.get("confidence")
            }
            for idx, t in enumerate(transcript)
        ]
        crud.create_transcripts_bulk(db, analysis_id, transcripts_for_db)

        # Save LLM insights
        crud.create_llm_insight(db, analysis_id, llm_insights)

        # Save key moments
        key_moments = identify_key_moments(emotion_data, gesture_data, transcript)
        key_moments_for_db = [
            {
                "timestamp": km["time"],
                "description": km["description"],
                "type": km["type"]
            }
            for km in key_moments
        ]
        crud.create_key_moments_bulk(db, analysis_id, key_moments_for_db)

        # Update analysis status to completed
        crud.update_analysis_status(db, analysis_id, AnalysisStatus.COMPLETED, progress=100)

        # Update video status
        crud.update_video_status(db, video_id, VideoStatus.COMPLETED)

        add_progress(str(analysis_id), "✅ Analysis completed successfully!")

        # Also save results to in-memory cache for backwards compatibility
        correlated_data = correlate_analysis(emotion_data, gesture_data, transcript, llm_insights)
        analysis_results[str(analysis_id)] = {
            "data": correlated_data,
            "video_path": f"http://localhost:8000/uploads/{video_path.name}"
        }

    except Exception as e:
        error_msg = f"❌ Error processing video: {str(e)}"
        add_progress(str(analysis_id), error_msg)
        analysis_errors[str(analysis_id)] = str(e)

        # Update database with error
        crud.update_analysis_status(
            db,
            analysis_id,
            AnalysisStatus.FAILED,
            error_message=str(e)
        )
        crud.update_video_status(db, video_id, VideoStatus.FAILED)
        print(error_msg)

    finally:
        db.close()


@app.post("/api/analyze")
async def analyze_video(
    video: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Main endpoint to analyze uploaded TED talk video

    Args:
        video: Uploaded video file
        db: Database session

    Returns:
        Analysis ID for tracking progress
    """
    try:
        # Validate file type
        if not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stored_filename = f"analysis_{timestamp}_{video.filename}"
        video_path = UPLOAD_DIR / stored_filename

        # Save uploaded video
        with video_path.open("wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # Get file size
        file_size = os.path.getsize(video_path)

        # Create video record in database
        db_video = crud.create_video(
            db=db,
            original_filename=video.filename,
            stored_filename=stored_filename,
            file_size=file_size,
        )

        # Create analysis record
        db_analysis = crud.create_analysis(db=db, video_id=db_video.id)

        # Initialize progress tracking (using string ID for backward compatibility)
        analysis_id_str = str(db_analysis.id)
        add_progress(analysis_id_str, f"📹 Uploading video: {video.filename}")
        add_progress(analysis_id_str, f"✅ Video uploaded successfully")

        # Update video status to processing
        crud.update_video_status(db, db_video.id, VideoStatus.PROCESSING)

        # Start background processing with UUID
        background_tasks.add_task(
            process_video_background,
            db_analysis.id,  # UUID
            db_video.id,  # UUID
            video_path,
            video.filename
        )

        # Return immediately with analysis ID
        return JSONResponse({
            "analysis_id": analysis_id_str,
            "status": "processing"
        })

    except Exception as e:
        print(f"Error processing video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/{analysis_id}")
async def get_results(analysis_id: str, db: Session = Depends(get_db)):
    """Get the results of a completed analysis"""
    try:
        # Convert string ID to UUID
        analysis_uuid = UUID(analysis_id)

        # Get analysis from database
        analysis = crud.get_analysis(db, analysis_uuid)

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Check status
        if analysis.status == AnalysisStatus.FAILED:
            raise HTTPException(status_code=500, detail=analysis.error_message or "Analysis failed")

        if analysis.status in [AnalysisStatus.PENDING, AnalysisStatus.PROCESSING]:
            return JSONResponse({"status": "processing", "progress": analysis.progress})

        # Get complete analysis data
        complete_data = crud.get_complete_analysis_data(db, analysis_uuid)

        if not complete_data:
            raise HTTPException(status_code=404, detail="Analysis data not found")

        return JSONResponse({
            "status": "completed",
            "data": complete_data,
            "video_path": complete_data["video_path"]
        })

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format")


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """
    Retrieve existing analysis results

    Args:
        analysis_id: Unique identifier for the analysis (UUID string)
        db: Database session

    Returns:
        Stored analysis results
    """
    try:
        # Convert string ID to UUID
        analysis_uuid = UUID(analysis_id)

        # Get complete analysis data from database
        data = crud.get_complete_analysis_data(db, analysis_uuid)

        if not data:
            raise HTTPException(status_code=404, detail="Analysis not found")

        return JSONResponse(data)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format")


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

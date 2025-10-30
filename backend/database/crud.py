"""
CRUD operations for GrowQR video analysis platform.
Handles Create, Read, Update, Delete operations for all models.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import (
    Video,
    Analysis,
    Emotion,
    Gesture,
    Transcript,
    LLMInsight,
    KeyMoment,
    VideoStatus,
    AnalysisStatus,
    EmotionType,
    GestureType,
    KeyMomentType,
)


# ============================================================================
# Video CRUD Operations
# ============================================================================

def create_video(
    db: Session,
    original_filename: str,
    stored_filename: str,
    file_size: int,
    duration: Optional[float] = None,
) -> Video:
    """Create a new video record"""
    video = Video(
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_size=file_size,
        duration=duration,
        status=VideoStatus.PENDING,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def get_video(db: Session, video_id: UUID) -> Optional[Video]:
    """Get video by ID"""
    return db.query(Video).filter(Video.id == video_id).first()


def get_video_by_filename(db: Session, stored_filename: str) -> Optional[Video]:
    """Get video by stored filename"""
    return db.query(Video).filter(Video.stored_filename == stored_filename).first()


def get_all_videos(db: Session, skip: int = 0, limit: int = 100) -> List[Video]:
    """Get all videos with pagination"""
    return db.query(Video).order_by(desc(Video.uploaded_at)).offset(skip).limit(limit).all()


def update_video_status(
    db: Session, video_id: UUID, status: VideoStatus, processed_at: Optional[datetime] = None
) -> Optional[Video]:
    """Update video status"""
    video = get_video(db, video_id)
    if video:
        video.status = status
        if processed_at:
            video.processed_at = processed_at
        elif status == VideoStatus.COMPLETED:
            video.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(video)
    return video


def delete_video(db: Session, video_id: UUID) -> bool:
    """Delete video (cascades to analyses)"""
    video = get_video(db, video_id)
    if video:
        db.delete(video)
        db.commit()
        return True
    return False


# ============================================================================
# Analysis CRUD Operations
# ============================================================================

def create_analysis(db: Session, video_id: UUID) -> Analysis:
    """Create a new analysis for a video"""
    analysis = Analysis(
        video_id=video_id,
        status=AnalysisStatus.PENDING,
        progress=0,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_analysis(db: Session, analysis_id: UUID) -> Optional[Analysis]:
    """Get analysis by ID with all relationships loaded"""
    return db.query(Analysis).filter(Analysis.id == analysis_id).first()


def get_analysis_by_video(db: Session, video_id: UUID) -> Optional[Analysis]:
    """Get latest analysis for a video"""
    return (
        db.query(Analysis)
        .filter(Analysis.video_id == video_id)
        .order_by(desc(Analysis.started_at))
        .first()
    )


def update_analysis_status(
    db: Session,
    analysis_id: UUID,
    status: AnalysisStatus,
    progress: Optional[int] = None,
    error_message: Optional[str] = None,
) -> Optional[Analysis]:
    """Update analysis status and progress"""
    analysis = get_analysis(db, analysis_id)
    if analysis:
        analysis.status = status
        if progress is not None:
            analysis.progress = progress
        if error_message:
            analysis.error_message = error_message
        if status == AnalysisStatus.COMPLETED:
            analysis.completed_at = datetime.utcnow()
            analysis.progress = 100
        db.commit()
        db.refresh(analysis)
    return analysis


def set_analysis_duration(db: Session, analysis_id: UUID, duration: float) -> Optional[Analysis]:
    """Set total duration for analysis"""
    analysis = get_analysis(db, analysis_id)
    if analysis:
        analysis.total_duration = duration
        db.commit()
        db.refresh(analysis)
    return analysis


# ============================================================================
# Emotion CRUD Operations
# ============================================================================

def create_emotions_bulk(
    db: Session, analysis_id: UUID, emotions_data: List[Dict[str, Any]]
) -> List[Emotion]:
    """
    Create multiple emotion records at once

    emotions_data format: [
        {"timestamp": 1.0, "emotion": "happy", "confidence": 0.85},
        {"timestamp": 2.0, "emotion": "confident", "confidence": 0.92},
        ...
    ]
    """
    emotions = []
    for data in emotions_data:
        emotion = Emotion(
            analysis_id=analysis_id,
            timestamp=data["timestamp"],
            emotion=EmotionType(data["emotion"]),
            confidence=data["confidence"],
        )
        emotions.append(emotion)

    db.bulk_save_objects(emotions)
    db.commit()
    return emotions


def get_emotions_by_analysis(db: Session, analysis_id: UUID) -> List[Emotion]:
    """Get all emotions for an analysis, ordered by timestamp"""
    return (
        db.query(Emotion)
        .filter(Emotion.analysis_id == analysis_id)
        .order_by(Emotion.timestamp)
        .all()
    )


# ============================================================================
# Gesture CRUD Operations
# ============================================================================

def create_gestures_bulk(
    db: Session, analysis_id: UUID, gestures_data: List[Dict[str, Any]]
) -> List[Gesture]:
    """
    Create multiple gesture records at once

    gestures_data format: [
        {"timestamp": 5.0, "type": "hand_raise", "description": "Raised hands for emphasis", "confidence": 0.88},
        ...
    ]
    """
    gestures = []
    for data in gestures_data:
        gesture = Gesture(
            analysis_id=analysis_id,
            timestamp=data["timestamp"],
            type=GestureType(data["type"]),
            description=data["description"],
            confidence=data["confidence"],
        )
        gestures.append(gesture)

    db.bulk_save_objects(gestures)
    db.commit()
    return gestures


def get_gestures_by_analysis(db: Session, analysis_id: UUID) -> List[Gesture]:
    """Get all gestures for an analysis, ordered by timestamp"""
    return (
        db.query(Gesture)
        .filter(Gesture.analysis_id == analysis_id)
        .order_by(Gesture.timestamp)
        .all()
    )


# ============================================================================
# Transcript CRUD Operations
# ============================================================================

def create_transcripts_bulk(
    db: Session, analysis_id: UUID, transcripts_data: List[Dict[str, Any]]
) -> List[Transcript]:
    """
    Create multiple transcript records at once

    transcripts_data format: [
        {"segment_index": 0, "start_time": 0.0, "end_time": 5.2, "text": "Hello everyone", "confidence": 0.95},
        ...
    ]
    """
    transcripts = []
    for data in transcripts_data:
        transcript = Transcript(
            analysis_id=analysis_id,
            segment_index=data.get("segment_index", 0),
            start_time=data["start_time"],
            end_time=data["end_time"],
            text=data["text"],
            confidence=data.get("confidence"),
        )
        transcripts.append(transcript)

    db.bulk_save_objects(transcripts)
    db.commit()
    return transcripts


def get_transcripts_by_analysis(db: Session, analysis_id: UUID) -> List[Transcript]:
    """Get all transcript segments for an analysis, ordered by start time"""
    return (
        db.query(Transcript)
        .filter(Transcript.analysis_id == analysis_id)
        .order_by(Transcript.start_time)
        .all()
    )


# ============================================================================
# LLM Insight CRUD Operations
# ============================================================================

def create_llm_insight(
    db: Session, analysis_id: UUID, insights_data: Dict[str, Any]
) -> LLMInsight:
    """
    Create LLM insights for an analysis

    insights_data format: {
        "main_topics": ["Leadership", "Innovation"],
        "rhetorical_techniques": ["Anecdotal Evidence", "Metaphor"],
        "argument_structure": "...",
        "persuasive_elements": ["Emotional Appeal", "Statistics"],
        "persuasion_score": 8.5,
        "overall_tone": "Inspirational and motivating",
        "transcript_summary": "The speaker discusses..."
    }
    """
    insight = LLMInsight(
        analysis_id=analysis_id,
        main_topics=insights_data.get("main_topics", []),
        rhetorical_techniques=insights_data.get("rhetorical_techniques", []),
        argument_structure=insights_data.get("argument_structure", ""),
        persuasive_elements=insights_data.get("persuasive_elements", []),
        persuasion_score=insights_data.get("persuasion_score", 5.0),
        overall_tone=insights_data.get("overall_tone", "Neutral"),
        transcript_summary=insights_data.get("transcript_summary", ""),
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


def get_llm_insight_by_analysis(db: Session, analysis_id: UUID) -> Optional[LLMInsight]:
    """Get LLM insights for an analysis"""
    return db.query(LLMInsight).filter(LLMInsight.analysis_id == analysis_id).first()


# ============================================================================
# Key Moment CRUD Operations
# ============================================================================

def create_key_moments_bulk(
    db: Session, analysis_id: UUID, moments_data: List[Dict[str, Any]]
) -> List[KeyMoment]:
    """
    Create multiple key moment records at once

    moments_data format: [
        {"timestamp": 45.0, "description": "Peak emotional moment", "type": "emotion"},
        {"timestamp": 120.0, "description": "Powerful gesture combined with speech", "type": "combined"},
        ...
    ]
    """
    moments = []
    for data in moments_data:
        moment = KeyMoment(
            analysis_id=analysis_id,
            timestamp=data["timestamp"],
            description=data["description"],
            type=KeyMomentType(data["type"]),
        )
        moments.append(moment)

    db.bulk_save_objects(moments)
    db.commit()
    return moments


def get_key_moments_by_analysis(db: Session, analysis_id: UUID) -> List[KeyMoment]:
    """Get all key moments for an analysis, ordered by timestamp"""
    return (
        db.query(KeyMoment)
        .filter(KeyMoment.analysis_id == analysis_id)
        .order_by(KeyMoment.timestamp)
        .all()
    )


# ============================================================================
# Complex Queries
# ============================================================================

def get_complete_analysis_data(db: Session, analysis_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get complete analysis data with all related entities
    Returns formatted dict matching the old JSON structure
    """
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        return None

    # Get all related data
    emotions = get_emotions_by_analysis(db, analysis_id)
    gestures = get_gestures_by_analysis(db, analysis_id)
    transcripts = get_transcripts_by_analysis(db, analysis_id)
    llm_insight = get_llm_insight_by_analysis(db, analysis_id)
    key_moments = get_key_moments_by_analysis(db, analysis_id)

    # Format emotions
    emotions_list = [
        {
            "time": emotion.timestamp,
            "emotion": emotion.emotion.value,
            "confidence": emotion.confidence,
        }
        for emotion in emotions
    ]

    # Format gestures
    gestures_list = [
        {
            "time": gesture.timestamp,
            "type": gesture.type.value,
            "description": gesture.description,
            "confidence": gesture.confidence,
        }
        for gesture in gestures
    ]

    # Format transcripts
    transcripts_list = [
        {
            "time": t.start_time,
            "end_time": t.end_time,
            "text": t.text,
            "confidence": t.confidence,
        }
        for t in transcripts
    ]

    # Format LLM insights
    llm_insights_dict = None
    if llm_insight:
        llm_insights_dict = {
            "main_topics": llm_insight.main_topics,
            "rhetorical_techniques": llm_insight.rhetorical_techniques,
            "argument_structure": llm_insight.argument_structure,
            "persuasive_elements": llm_insight.persuasive_elements,
            "persuasion_score": llm_insight.persuasion_score,
            "overall_tone": llm_insight.overall_tone,
            "transcript_summary": llm_insight.transcript_summary,
        }

    # Format key moments
    key_moments_list = [
        {
            "time": moment.timestamp,
            "description": moment.description,
            "type": moment.type.value,
        }
        for moment in key_moments
    ]

    # Calculate emotional range
    emotional_range = list(set([e.emotion.value for e in emotions])) if emotions else []

    # Build summary
    summary = {
        "total_duration": analysis.total_duration or 0,
        "emotional_range": emotional_range,
        "key_moments": key_moments_list,
        "top_themes": llm_insight.main_topics if llm_insight else [],
    }

    return {
        "emotions": emotions_list,
        "gestures": gestures_list,
        "transcript": transcripts_list,
        "llm_insights": llm_insights_dict,
        "summary": summary,
        "video_path": f"http://localhost:8000/uploads/{analysis.video.stored_filename}",
    }


def search_analyses_by_topic(db: Session, topic: str, limit: int = 10) -> List[Analysis]:
    """Search analyses by topic in LLM insights"""
    return (
        db.query(Analysis)
        .join(LLMInsight)
        .filter(LLMInsight.main_topics.contains([topic]))
        .order_by(desc(Analysis.completed_at))
        .limit(limit)
        .all()
    )


def get_high_persuasion_analyses(db: Session, min_score: float = 8.0, limit: int = 10) -> List[Analysis]:
    """Get analyses with high persuasion scores"""
    return (
        db.query(Analysis)
        .join(LLMInsight)
        .filter(LLMInsight.persuasion_score >= min_score)
        .order_by(desc(LLMInsight.persuasion_score))
        .limit(limit)
        .all()
    )

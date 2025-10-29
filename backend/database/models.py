"""
SQLAlchemy ORM models for GrowQR video analysis platform.
"""

import enum
from datetime import datetime
from typing import List
import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Enum,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class VideoStatus(str, enum.Enum):
    """Video processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisStatus(str, enum.Enum):
    """Analysis status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EmotionType(str, enum.Enum):
    """Emotion types detected in video"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SERIOUS = "serious"
    PASSIONATE = "passionate"
    CONFIDENT = "confident"
    HOPEFUL = "hopeful"


class GestureType(str, enum.Enum):
    """Gesture types detected in video"""
    HAND_RAISE = "hand_raise"
    POINTING = "pointing"
    OPEN_ARMS = "open_arms"
    HAND_GESTURE = "hand_gesture"


class KeyMomentType(str, enum.Enum):
    """Key moment types"""
    EMOTION = "emotion"
    GESTURE = "gesture"
    COMBINED = "combined"


class Video(Base):
    """
    Video model - stores metadata about uploaded videos
    """
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    file_size = Column(Integer, nullable=False)  # bytes
    duration = Column(Float, nullable=True)  # seconds
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    analyses = relationship("Analysis", back_populates="video", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_video_status", "status"),
        Index("idx_video_uploaded_at", "uploaded_at"),
    )

    def __repr__(self):
        return f"<Video(id={self.id}, filename={self.original_filename}, status={self.status})>"


class Analysis(Base):
    """
    Analysis model - represents a complete analysis of a video
    """
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False)
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    total_duration = Column(Float, nullable=True)  # seconds

    # Relationships
    video = relationship("Video", back_populates="analyses")
    emotions = relationship("Emotion", back_populates="analysis", cascade="all, delete-orphan")
    gestures = relationship("Gesture", back_populates="analysis", cascade="all, delete-orphan")
    transcripts = relationship("Transcript", back_populates="analysis", cascade="all, delete-orphan")
    llm_insight = relationship("LLMInsight", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    key_moments = relationship("KeyMoment", back_populates="analysis", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_analysis_video_id", "video_id"),
        Index("idx_analysis_status", "status"),
        Index("idx_analysis_started_at", "started_at"),
    )

    def __repr__(self):
        return f"<Analysis(id={self.id}, video_id={self.video_id}, status={self.status})>"


class Emotion(Base):
    """
    Emotion model - stores emotion data points throughout the video
    """
    __tablename__ = "emotions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(Float, nullable=False)  # seconds
    emotion = Column(Enum(EmotionType), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0-1.0
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis = relationship("Analysis", back_populates="emotions")

    # Indexes
    __table_args__ = (
        Index("idx_emotion_analysis_id", "analysis_id"),
        Index("idx_emotion_timestamp", "timestamp"),
        Index("idx_emotion_type", "emotion"),
    )

    def __repr__(self):
        return f"<Emotion(id={self.id}, time={self.timestamp}s, emotion={self.emotion}, conf={self.confidence:.2f})>"


class Gesture(Base):
    """
    Gesture model - stores gesture detection data throughout the video
    """
    __tablename__ = "gestures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(Float, nullable=False)  # seconds
    type = Column(Enum(GestureType), nullable=False)
    description = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0-1.0
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis = relationship("Analysis", back_populates="gestures")

    # Indexes
    __table_args__ = (
        Index("idx_gesture_analysis_id", "analysis_id"),
        Index("idx_gesture_timestamp", "timestamp"),
        Index("idx_gesture_type", "type"),
    )

    def __repr__(self):
        return f"<Gesture(id={self.id}, time={self.timestamp}s, type={self.type}, conf={self.confidence:.2f})>"


class Transcript(Base):
    """
    Transcript model - stores speech transcription segments
    """
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    segment_index = Column(Integer, nullable=False)
    start_time = Column(Float, nullable=False)  # seconds
    end_time = Column(Float, nullable=False)  # seconds
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis = relationship("Analysis", back_populates="transcripts")

    # Indexes
    __table_args__ = (
        Index("idx_transcript_analysis_id", "analysis_id"),
        Index("idx_transcript_start_time", "start_time"),
    )

    def __repr__(self):
        return f"<Transcript(id={self.id}, time={self.start_time}s-{self.end_time}s, text='{self.text[:30]}...')>"


class LLMInsight(Base):
    """
    LLM Insight model - stores AI-generated insights about the content
    """
    __tablename__ = "llm_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, unique=True)
    main_topics = Column(JSONB, nullable=False)  # Array of strings
    rhetorical_techniques = Column(JSONB, nullable=False)  # Array of strings
    argument_structure = Column(Text, nullable=True)
    persuasive_elements = Column(JSONB, nullable=False)  # Array of strings
    persuasion_score = Column(Float, nullable=False)  # 1-10
    overall_tone = Column(Text, nullable=False)
    transcript_summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis = relationship("Analysis", back_populates="llm_insight")

    # Indexes
    __table_args__ = (
        Index("idx_llm_insight_analysis_id", "analysis_id"),
        Index("idx_llm_insight_persuasion_score", "persuasion_score"),
    )

    def __repr__(self):
        return f"<LLMInsight(id={self.id}, analysis_id={self.analysis_id}, score={self.persuasion_score})>"


class KeyMoment(Base):
    """
    Key Moment model - stores significant moments identified in the video
    """
    __tablename__ = "key_moments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(Float, nullable=False)  # seconds
    description = Column(Text, nullable=False)
    type = Column(Enum(KeyMomentType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis = relationship("Analysis", back_populates="key_moments")

    # Indexes
    __table_args__ = (
        Index("idx_key_moment_analysis_id", "analysis_id"),
        Index("idx_key_moment_timestamp", "timestamp"),
    )

    def __repr__(self):
        return f"<KeyMoment(id={self.id}, time={self.timestamp}s, type={self.type})>"

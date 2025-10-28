"""
Audio processing module using Whisper
Handles audio extraction and speech-to-text transcription
"""

import whisper
from pathlib import Path
from typing import List, Dict
import subprocess


class AudioProcessor:
    """Process audio for transcription and analysis"""

    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper model

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
                       'base' is a good balance of speed and accuracy
        """
        print(f"Loading Whisper model: {model_size}")
        try:
            self.model = whisper.load_model(model_size)
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            print("Falling back to 'base' model")
            self.model = whisper.load_model("base")

    def extract_audio(self, video_path: str) -> str:
        """
        Extract audio track from video file

        Args:
            video_path: Path to video file

        Returns:
            Path to extracted audio file
        """
        video_path = Path(video_path)
        audio_path = video_path.parent / f"{video_path.stem}_audio.wav"

        print(f"Extracting audio from {video_path}")

        try:
            # Use ffmpeg to extract audio
            command = [
                'ffmpeg',
                '-i', str(video_path),
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM 16-bit
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite output
                str(audio_path)
            ]

            subprocess.run(command, check=True, capture_output=True)
            print(f"Audio extracted to {audio_path}")
            return str(audio_path)

        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e}")
            raise Exception(f"Failed to extract audio: {e.stderr.decode()}")

    def transcribe(self, audio_path: str) -> List[Dict]:
        """
        Transcribe audio to text with timestamps

        Args:
            audio_path: Path to audio file

        Returns:
            List of transcribed segments with timestamps
        """
        print(f"Transcribing audio: {audio_path}")

        try:
            # Transcribe with word-level timestamps
            result = self.model.transcribe(
                audio_path,
                language="en",
                word_timestamps=True,
                verbose=False
            )

            # Format transcript with timestamps
            transcript = []

            for segment in result["segments"]:
                transcript.append({
                    "time": round(segment["start"]),
                    "end_time": round(segment["end"]),
                    "text": segment["text"].strip(),
                    "confidence": segment.get("avg_logprob", 0)
                })

            print(f"Transcribed {len(transcript)} segments")
            return transcript

        except Exception as e:
            print(f"Error transcribing audio: {e}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")

    def analyze_voice_tone(self, audio_path: str) -> Dict:
        """
        Analyze voice characteristics (pitch, volume, speaking rate)

        Args:
            audio_path: Path to audio file

        Returns:
            Voice analysis metrics
        """
        # This would use audio analysis libraries like librosa
        # For now, returning placeholder structure

        return {
            "average_pitch": 0,
            "pitch_variance": 0,
            "average_volume": 0,
            "speaking_rate": 0,  # words per minute
            "pauses": [],
            "emphasis_points": []
        }

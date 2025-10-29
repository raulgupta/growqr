#!/usr/bin/env python3
"""
Clear all data from GrowQR database

Usage:
    python scripts/clear_database.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_db
from database.models import (
    Video, Analysis, Emotion, Gesture,
    Transcript, LLMInsight, KeyMoment
)


def clear_all_data():
    """Delete all data from all tables"""
    db = next(get_db())

    try:
        print("🗑️  Clearing all data from database...")

        # Delete in correct order (children first)
        tables = [
            (KeyMoment, "key_moments"),
            (LLMInsight, "llm_insights"),
            (Transcript, "transcripts"),
            (Gesture, "gestures"),
            (Emotion, "emotions"),
            (Analysis, "analyses"),
            (Video, "videos"),
        ]

        for model, name in tables:
            count = db.query(model).count()
            if count > 0:
                db.query(model).delete()
                print(f"  ✓ Deleted {count} rows from {name}")
            else:
                print(f"  - {name} was already empty")

        db.commit()
        print("\n✅ All data cleared successfully!")
        print("\n📊 Database is now empty and ready for new analyses.")

    except Exception as e:
        print(f"\n❌ Error clearing database: {e}")
        db.rollback()
    finally:
        db.close()


def confirm_action():
    """Ask user to confirm before deleting data"""
    print("⚠️  WARNING: This will delete ALL data from the database!")
    print("   - All videos")
    print("   - All analyses")
    print("   - All emotions, gestures, transcripts")
    print("   - All LLM insights and key moments")
    print()

    response = input("Are you sure you want to continue? (yes/no): ")
    return response.lower() in ['yes', 'y']


if __name__ == "__main__":
    if confirm_action():
        clear_all_data()
    else:
        print("\n❌ Operation cancelled.")

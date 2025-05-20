# backend/youtube/get_transcript.py

from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional, List, Dict
import os
import sys
import json
import logging
from datetime import datetime
import re

# Add the backend directory to Python path using relative path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend/logs/transcript_downloader.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class YouTubeTranscriptDownloader:
    def __init__(self, languages: List[str] = ["ja", "en"]):
        """Initialize the transcript downloader"""
        self.languages = languages

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        try:
            if "v=" in url:
                return url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                return url.split("youtu.be/")[1].split("?")[0]
            return None
        except Exception as e:
            logger.error(f"Error extracting video ID: {str(e)}")
            return None

    def get_transcript(self, video_id: str) -> Optional[List[Dict]]:
        """Download transcript from YouTube"""
        try:
            # Extract video ID if full URL is provided
            if "youtube.com" in video_id or "youtu.be" in video_id:
                video_id = self.extract_video_id(video_id)

            if not video_id:
                raise ValueError("Invalid video ID or URL")

            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=self.languages
            )
            logger.info(f"Successfully downloaded transcript for video {video_id}")
            return transcript
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            return None

    def save_transcript(self, transcript: List[Dict], video_id: str) -> bool:
        """Save transcript to file in JSON format"""
        try:
            # Create transcript data structure matching database schema
            transcript_data = {
                "video_id": video_id,
                "transcript": "\n".join(entry["text"] for entry in transcript),
                "language": "ja",  # Default to Japanese
                "created_at": datetime.now().isoformat()
            }

            # Save as JSON file
            file_path = get_file_path("data/transcripts", video_id, "json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Transcript saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving transcript: {str(e)}")
            return False

    def process_video(self, video_url: str) -> Optional[Dict]:
        """Process a video URL and return transcript data"""
        try:
            video_id = self.extract_video_id(video_url)
            if not video_id:
                logger.error("Invalid video URL")
                return None

            transcript = self.get_transcript(video_id)
            if not transcript:
                logger.error("Failed to get transcript")
                return None

            if self.save_transcript(transcript, video_id):
                return {
                    "video_id": video_id,
                    "transcript": transcript
                }
            return None
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            return None

    def validate_content(self, transcript: str) -> bool:
        """
        Validate transcript content for appropriateness.
        Returns True if content is appropriate, False otherwise.
        """
        try:
            # Load inappropriate content patterns
            inappropriate_patterns = [
                r'暴力|暴行|殺人|自殺|虐待',  # Violence
                r'性的|ポルノ|ヌード',  # Sexual content
                r'差別|ヘイト|侮辱',  # Discrimination
                r'違法|犯罪|麻薬|薬物',  # Illegal activities
                r'過度な下品|過度な卑猥',  # Excessive vulgarity
            ]
            
            # Check for inappropriate content
            for pattern in inappropriate_patterns:
                if re.search(pattern, transcript, re.IGNORECASE):
                    logger.warning(f"Content validation failed: Inappropriate content detected: {pattern}")
                    return False
            
            # Check for minimum content length
            if len(transcript) < 50:
                logger.warning("Content validation failed: Transcript too short")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating content: {str(e)}")
            return False
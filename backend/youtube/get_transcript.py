# backend/youtube/get_transcript.py

from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional, List, Dict
# import os
import sys
sys.path.insert(0, '/home/sage/free-genai-bootcamp-2025/listening-speaking/backend')
from backend.utils.helper import get_file_path

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
        except Exception:
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
            return transcript
        except Exception as e:
            print(f"Error getting transcript: {str(e)}")
            return None

    def save_transcript(self, transcript: List[Dict], video_id: str) -> bool:
        """Save transcript to file"""
        try:
            # Save as text file
            file_path = get_file_path("data/transcripts", video_id, "txt")

            with open(file_path, 'w', encoding='utf-8') as f:
                for entry in transcript:
                    f.write(f"{entry['text']}\n")

            print(f"Transcript saved to {file_path}")
            return True
        except Exception as e:
            print(f"Error saving transcript: {str(e)}")
            return False

    def process_video(self, video_url: str) -> Optional[Dict]:
        """Process a video URL and return transcript data"""
        video_id = self.extract_video_id(video_url)
        if not video_id:
            print("Invalid video URL")
            return None

        transcript = self.get_transcript(video_id)
        if not transcript:
            print("Failed to get transcript")
            return None

        if self.save_transcript(transcript, video_id):
            return {
                "video_id": video_id,
                "transcript": transcript
            }
        return None
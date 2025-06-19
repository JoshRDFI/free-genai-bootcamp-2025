# backend/youtube/get_transcript.py

from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional, List, Dict
import os
import sys
import json
import logging
from datetime import datetime
from backend.utils.helper import get_file_path
from backend.asr.asr_engine import ASREngine  # Import the correct ASR engine
import yt_dlp  # For downloading audio

# Add the backend directory to Python path using relative path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "transcript_downloader.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class YouTubeTranscriptDownloader:
    def __init__(self, languages: List[str] = ["ja", "en"]):
        """Initialize the transcript downloader"""
        self.languages = languages
        self.asr = ASREngine()  # Initialize ASR engine

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

    def download_audio(self, video_id: str) -> Optional[str]:
        """Download audio from YouTube video"""
        try:
            logger.info(f"Starting audio download for video {video_id}")
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
                'outtmpl': f'temp_{video_id}.%(ext)s',
                'quiet': False,  # Enable logging to see what's happening
                'no_warnings': False
            }

            # Download audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Downloading audio with yt-dlp...")
                ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
                
                # Check if the file was created
                expected_file = f'temp_{video_id}.wav'
                if os.path.exists(expected_file):
                    logger.info(f"Audio file downloaded successfully: {expected_file}")
                    return expected_file
                else:
                    logger.error(f"Audio file not found after download: {expected_file}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            return None

    def get_transcript(self, video_id_or_url: str) -> Optional[List[Dict]]:
        """Download transcript from YouTube or generate using ASR"""
        try:
            # Extract video ID if full URL is provided
            if "youtube.com" in video_id_or_url or "youtu.be" in video_id_or_url:
                video_id = self.extract_video_id(video_id_or_url)
            else:
                video_id = video_id_or_url

            if not video_id:
                raise ValueError("Invalid video ID or URL")

            logger.info(f"Attempting to get transcript for video {video_id}")
            
            # Try to get Japanese transcript first
            try:
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id,
                    languages=['ja']
                )
                logger.info(f"Successfully downloaded Japanese transcript for video {video_id}")
                return transcript
            except Exception as e:
                logger.warning(f"No Japanese transcript available: {str(e)}")
                logger.info("Attempting to generate transcript using ASR...")
                
                # If no transcript available, use ASR to generate one
                try:
                    # Download audio
                    audio_file = self.download_audio(video_id)
                    if not audio_file:
                        logger.error("Failed to download audio")
                        return None

                    logger.info(f"Starting ASR transcription for file: {audio_file}")
                    
                    # Check file size and format
                    if os.path.exists(audio_file):
                        file_size = os.path.getsize(audio_file)
                        logger.info(f"Audio file size: {file_size} bytes")
                        if file_size == 0:
                            logger.error("Audio file is empty")
                            return None
                    else:
                        logger.error(f"Audio file does not exist: {audio_file}")
                        return None

                    # Transcribe using ASR
                    result = self.asr.transcribe_file(audio_file, language="ja")
                    
                    logger.info(f"ASR result: {result}")
                    
                    # Clean up temporary audio file
                    try:
                        os.remove(audio_file)
                        logger.info(f"Cleaned up temporary audio file: {audio_file}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up audio file: {cleanup_error}")

                    if result and "text" in result:
                        # Convert ASR result to YouTube transcript format
                        # ASR returns a single text block, so we'll create one segment
                        transcript = [
                            {
                                "text": result["text"],
                                "start": 0,
                                "duration": 0
                            }
                        ]
                        logger.info(f"Successfully generated Japanese transcript using ASR for video {video_id}")
                        return transcript
                    else:
                        logger.error("ASR transcription failed or returned invalid format")
                        return None
                except Exception as e2:
                    logger.error(f"Error generating transcript with ASR: {str(e2)}")
                    return None
        except Exception as e:
            logger.error(f"Error in get_transcript: {str(e)}")
            return None

    def save_transcript(self, transcript: List[Dict], video_id: str) -> bool:
        """Save transcript to file in JSON format"""
        try:
            # Create transcript data structure matching database schema
            transcript_data = {
                "video_id": video_id,
                "transcript": "\n".join(entry["text"] for entry in transcript),
                "language": "ja",  # Always Japanese
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
                logger.error("Failed to get or generate transcript")
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
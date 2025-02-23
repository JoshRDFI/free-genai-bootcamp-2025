# backend/app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn

from backend.youtube.get_transcript import YouTubeTranscriptDownloader
from backend.llm.question_generator import QuestionGenerator
from backend.database.knowledge_base import KnowledgeBase
from backend.utils.helper import ensure_directories_exist

app = FastAPI()

# Initialize components
transcript_downloader = YouTubeTranscriptDownloader()
question_generator = QuestionGenerator()
knowledge_base = KnowledgeBase()

# Ensure required directories exist
ensure_directories_exist()

class VideoURL(BaseModel):
    url: str

class Question(BaseModel):
    video_id: str
    section_num: int
    question_text: str

@app.post("/process-video")
async def process_video(video_data: VideoURL):
    """Process a YouTube video URL"""
    try:
        # Get transcript
        result = transcript_downloader.process_video(video_data.url)
        if not result:
            raise HTTPException(status_code=400, detail="Failed to process video")

        # Save to database
        video_id = result["video_id"]
        transcript_text = "\n".join(item["text"] for item in result["transcript"])
        knowledge_base.save_transcript(video_id, transcript_text)

        # Generate questions
        questions = question_generator.generate_questions(result["transcript"], video_id)

        # Save questions
        for question in questions:
            knowledge_base.save_question(question)

        return {"status": "success", "video_id": video_id, "question_count": len(questions)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/questions/{video_id}")
async def get_questions(video_id: str):
    """Get questions for a video"""
    questions = knowledge_base.get_questions(video_id)
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found")
    return questions

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
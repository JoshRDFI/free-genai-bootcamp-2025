import json
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_relative(path):
    # Only keep the filename for portability
    return os.path.basename(path)

def update_stored_questions():
    """Update stored_questions.json to use the new image format with relative paths for all images fields"""
    try:
        # Get the path to stored_questions.json
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        questions_file = project_root / "backend" / "data" / "stored_questions.json"
        
        if not questions_file.exists():
            logger.error(f"Questions file not found at {questions_file}")
            return False
            
        # Load existing questions
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
            
        # Update each question
        for qid, qdata in questions.items():
            try:
                question = qdata.get("question", {})
                # Handle legacy 'image_path' field
                old_image_path = question.get("image_path")
                if old_image_path:
                    images = {}
                    base_name = Path(old_image_path).stem
                    for i, option in enumerate(question.get("Options", [])):
                        option_letter = chr(65 + i)
                        new_image_filename = f"{base_name}_option_{option_letter}.png"
                        images[option_letter] = new_image_filename
                    question["images"] = images
                    question.pop("image_path", None)
                    logger.info(f"Updated question {qid} from legacy image_path to images (relative paths)")
                # Convert all images fields to relative paths
                if "images" in question:
                    for k, v in list(question["images"].items()):
                        question["images"][k] = make_relative(v)
                    logger.info(f"Normalized images paths for question {qid}")
            except Exception as e:
                logger.error(f"Error updating question {qid}: {str(e)}")
                continue
        # Save updated questions
        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        logger.info("Successfully updated stored_questions.json with relative image paths for all images fields")
        return True
    except Exception as e:
        logger.error(f"Error updating stored questions: {str(e)}")
        return False

if __name__ == "__main__":
    update_stored_questions() 
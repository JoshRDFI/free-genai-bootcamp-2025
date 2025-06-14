"""
Grading module for Japanese text input.
"""
import requests
from typing import Optional, Dict
from ..utils.logging import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)

class Grader:
    """Handles grading of Japanese text input."""
    
    def __init__(self):
        """Initialize the grader."""
        self.config = get_config()
        self.endpoint = self.config.get('ollama_endpoint', 'http://localhost:11434/api/generate')
        self.model = self.config.get('ollama_model', 'llama3.2')
    
    def grade(self, submission: str, target: str, translation: str) -> Optional[Dict[str, str]]:
        """
        Grade a Japanese text submission against a target.
        
        Args:
            submission: Submitted Japanese text
            target: Target Japanese text
            translation: English translation of the submission
            
        Returns:
            Dictionary containing grade and feedback, or None if grading fails
        """
        try:
            prompts = self.config.get('prompts', {})
            system_prompt = prompts.get('grading', {}).get('system', '')
            user_prompt = prompts.get('grading', {}).get('user', '').format(
                submission=submission,
                target=target,
                translation=translation
            )
            
            # First LLM call for grading
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Parse grade and feedback
                lines = response_text.strip().split('\n')
                grade = None
                feedback = []
                
                for line in lines:
                    if line.startswith("Grade:"):
                        grade = line.replace("Grade:", "").strip().upper()
                        # Validate grade is in correct format
                        if grade not in ['S', 'A', 'B', 'C', 'D', 'F']:
                            grade = None
                    elif line.startswith("Feedback:"):
                        feedback.append(line.replace("Feedback:", "").strip())
                
                if grade and feedback:
                    return {
                        "grade": grade,
                        "feedback": "\n".join(feedback),
                        "translation": translation
                    }
                else:
                    logger.warning("LLM response did not contain expected grade/feedback format")
                    return self._fallback_grade(submission, target, translation)
            
            logger.error(f"LLM API error: {response.status_code} {response.text}")
            return self._fallback_grade(submission, target, translation)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API request failed: {e}")
            return self._fallback_grade(submission, target, translation)
        except Exception as e:
            logger.error(f"Grading error: {e}")
            return self._fallback_grade(submission, target, translation)
    
    def _fallback_grade(self, submission: str, target: str, translation: str) -> Dict[str, str]:
        """
        Fallback grading method using character similarity.
        
        Args:
            submission: Submitted Japanese text
            target: Target Japanese text
            translation: English translation of the submission
            
        Returns:
            Dictionary containing grade and feedback
        """
        if not submission.strip():
            return {
                "grade": "F",
                "feedback": "No submission provided.",
                "translation": translation
            }
        
        # Calculate character similarity
        submission_chars = set(submission)
        target_chars = set(target)
        similarity = len(submission_chars & target_chars) / len(target_chars)
        
        # Determine grade using Japanese-style grading
        if similarity > 0.95:
            grade = "S"  # Superior
        elif similarity > 0.85:
            grade = "A"  # Excellent
        elif similarity > 0.75:
            grade = "B"  # Good
        elif similarity > 0.65:
            grade = "C"  # Average
        elif similarity > 0.50:
            grade = "D"  # Below Average
        else:
            grade = "F"  # Failed
        
        return {
            "grade": grade,
            "feedback": f"Character similarity: {int(similarity * 100)}%",
            "translation": translation
        }

    def is_available(self) -> bool:
        """Check if the LLM service is available."""
        try:
            response = requests.get(
                self.endpoint.rsplit('/api/', 1)[0] + '/api/version',
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False

# Create singleton instance
_grader = None

def get_grader() -> Grader:
    """Get the singleton grader instance."""
    global _grader
    if _grader is None:
        _grader = Grader()
    return _grader 
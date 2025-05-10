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
    
    def grade(self, submission: str, target: str) -> Optional[Dict[str, str]]:
        """
        Grade a Japanese text submission against a target.
        
        Args:
            submission: Submitted Japanese text
            target: Target Japanese text
            
        Returns:
            Dictionary containing grade and feedback, or None if grading fails
        """
        try:
            prompts = self.config.get('prompts', {})
            system_prompt = prompts.get('grading', {}).get('system', '')
            user_prompt = prompts.get('grading', {}).get('user', '').format(
                submission=submission,
                target=target
            )
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False
                },
                timeout=10
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
                        grade = line.replace("Grade:", "").strip()
                    elif line.startswith("Feedback:"):
                        feedback.append(line.replace("Feedback:", "").strip())
                
                if grade and feedback:
                    return {
                        "grade": grade,
                        "feedback": "\n".join(feedback)
                    }
            
            # Fallback grading
            return self._fallback_grade(submission, target)
                
        except Exception as e:
            logger.error(f"Grading error: {e}")
            return self._fallback_grade(submission, target)
    
    def _fallback_grade(self, submission: str, target: str) -> Dict[str, str]:
        """
        Fallback grading method using character similarity.
        
        Args:
            submission: Submitted Japanese text
            target: Target Japanese text
            
        Returns:
            Dictionary containing grade and feedback
        """
        if not submission.strip():
            return {
                "grade": "F",
                "feedback": "No submission provided."
            }
        
        # Calculate character similarity
        submission_chars = set(submission)
        target_chars = set(target)
        similarity = len(submission_chars & target_chars) / len(target_chars)
        
        # Determine grade
        if similarity > 0.9:
            grade = "A"
        elif similarity > 0.7:
            grade = "B"
        elif similarity > 0.5:
            grade = "C"
        else:
            grade = "F"
        
        return {
            "grade": grade,
            "feedback": f"Character similarity: {int(similarity * 100)}%"
        }

# Create singleton instance
_grader = None

def get_grader() -> Grader:
    """Get the singleton grader instance."""
    global _grader
    if _grader is None:
        _grader = Grader()
    return _grader 
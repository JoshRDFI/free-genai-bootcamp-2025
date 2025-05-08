# Python package for the Japanese Learning Visual Novel

from .api import APIService
from .jlpt import JLPTCurriculum
from .progress import ProgressTracker

# Initialize global instances
api_service = APIService()
jlpt_curriculum = JLPTCurriculum()
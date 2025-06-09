# backend/guardrails/rules.py

import re
from typing import Dict, List, Optional, Tuple

class ContentGuardrails:
    def __init__(self):
        """Initialize content filtering rules"""
        # Inappropriate content patterns - more context-aware
        self.inappropriate_patterns = [
            r'(?i)(殺人|殺害|殺戮)',  # Explicit killing/violence
            r'(?i)(暴力|暴行|虐待)',  # Violence, assault, abuse
            r'(?i)(セックス|ポルノ|性的)',  # Adult content
            r'(?i)(麻薬|違法薬物)',  # Drugs
            r'(?i)(差別|人種差別|ヘイトスピーチ)',  # Discrimination, hate speech
        ]

        # Question structure requirements
        self.required_fields = [
            'Introduction',
            'Conversation',
            'Question',
            'Options'
        ]

        # Japanese text validation
        self.japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')

    def validate_japanese_text(self, text: str) -> bool:
        """
        Validate that text contains Japanese characters.
        """
        return bool(self.japanese_pattern.search(text))

    def check_inappropriate_content(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check for inappropriate content in text.
        Returns (is_safe, reason_if_unsafe)
        """
        for pattern in self.inappropriate_patterns:
            match = re.search(pattern, text)
            if match:
                return False, f"Inappropriate content detected: {match.group()}"
        return True, None

    def validate_question_format(self, question: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate question format and structure.
        Returns (is_valid, reason_if_invalid)
        """
        # Check required fields
        for field in self.required_fields:
            if field not in question:
                return False, f"Missing required field: {field}"

        # Validate Japanese content in each field
        for field in ['Introduction', 'Conversation', 'Question']:
            if not self.validate_japanese_text(question[field]):
                return False, f"No Japanese text found in {field}"

        # Validate options
        if not isinstance(question.get('Options'), list):
            return False, "Options must be a list"

        if len(question['Options']) != 4:
            return False, "Must have exactly 4 options"

        for option in question['Options']:
            if not self.validate_japanese_text(str(option)):
                return False, "All options must contain Japanese text"

        return True, None

    def validate_transcript(self, transcript: str) -> Tuple[bool, Optional[str]]:
        """
        Validate transcript content.
        Returns (is_valid, reason_if_invalid)
        """
        if not transcript:
            return False, "Empty transcript"

        # Check for Japanese content
        if not self.validate_japanese_text(transcript):
            return False, "No Japanese text found in transcript"

        # Check for inappropriate content
        is_safe, reason = self.check_inappropriate_content(transcript)
        if not is_safe:
            return False, reason

        # Check minimum length (e.g., 50 characters)
        if len(transcript) < 50:
            return False, "Transcript too short"

        return True, None

    def validate_audio_text(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate text before audio generation.
        Returns (is_valid, reason_if_invalid)
        """
        if not text:
            return False, "Empty text"

        # Check for Japanese content
        if not self.validate_japanese_text(text):
            return False, "No Japanese text found"

        # Check for inappropriate content
        is_safe, reason = self.check_inappropriate_content(text)
        if not is_safe:
            return False, reason

        # Check maximum length (e.g., 500 characters)
        if len(text) > 500:
            return False, "Text too long for audio generation"

        return True, None

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text by removing or replacing problematic content.
        """
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32)

        # Remove multiple spaces
        text = ' '.join(text.split())

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        return text.strip()
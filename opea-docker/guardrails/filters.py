import re
from typing import Tuple, List, Dict, Any, Optional
from better_profanity import profanity
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from config import config

# Initialize profanity filter
profanity.load_censor_words()

class ContentFilter:
    def __init__(self):
        self.forbidden_words = config.forbidden_words
        self.forbidden_patterns = [
            r'\b(?:how\s+to|instructions\s+for)\s+(?:make|create|build)\s+(?:bomb|explosive|weapon)',
            r'\b(?:hack|steal|access)\s+(?:account|password|data|information)',
            r'\b(?:child|minor)\s+(?:porn|pornography|explicit)',
            r'\b(?:buy|purchase|obtain)\s+(?:illegal\s+drugs|cocaine|heroin|meth)',
            r'\b(?:plan|execute)\s+(?:attack|terrorism|violent)',
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.forbidden_patterns]

    def detect_language(self, text: str) -> Optional[str]:
        """Detect the language of the text."""
        return detect(text)


    def is_language_supported(self, text: str) -> bool:
        """Check if the language of the text is supported."""
        if not config.multi_language_enabled:
            return True

        lang = self.detect_language(text)
        if not lang:
            return True  # If we can't detect the language, assume it's supported

        return lang in config.supported_languages

    def contains_forbidden_words(self, text: str) -> Tuple[bool, str]:
        """Check if the text contains any forbidden words."""
        text_lower = text.lower()
        for word in self.forbidden_words:
            if word in text_lower:
                return True, f"Content contains forbidden word: {word}"
        return False, ""

    def contains_forbidden_patterns(self, text: str) -> Tuple[bool, str]:
        """Check if the text matches any forbidden patterns."""
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(text):
                return True, f"Content matches forbidden pattern {i+1}"
        return False, ""

    def contains_profanity(self, text: str) -> Tuple[bool, str]:
        """Check if the text contains profanity."""
        if profanity.contains_profanity(text):
            return True, "Content contains profanity"
        return False, ""

    def analyze_intent(self, text: str) -> Tuple[bool, str]:
        """Analyze the intent of the text using simple keyword matching."""
        text_lower = text.lower()

        # Check for potentially harmful intents using simple keyword matching
        harmful_verbs = ["kill", "hurt", "harm", "attack", "destroy", "damage", "murder", "assassinate"]
        harmful_patterns = [
            r'\b(?:' + '|'.join(harmful_verbs) + r')\s+(?:someone|people|person|human|humans)',
            r'\b(?:want|going|plan)\s+to\s+(?:' + '|'.join(harmful_verbs) + r')',
            r'\bhow\s+to\s+(?:' + '|'.join(harmful_verbs) + r')',
        ]

        for pattern in harmful_patterns:
            if re.search(pattern, text_lower):
                return True, "Content contains potentially harmful intent"

        return False, ""

    def analyze_context(self, messages: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Analyze the conversation context for potential policy violations."""
        if not config.context_moderation_enabled or len(messages) < 2:
            return False, ""

        # Get the last N messages for context analysis
        context_messages = messages[-min(len(messages), config.max_context_length):]
        combined_text = " ".join([msg["content"] for msg in context_messages])

        # Check for attempts to circumvent filters through context
        circumvention_patterns = [
            r"\b(?:ignore|disregard)\s+(?:previous|earlier|above)\s+(?:instructions|rules|guidelines)",
            r"\b(?:pretend|act)\s+(?:as if|like)\s+(?:you are|you're)\s+(?:not|no longer)\s+(?:bound|restricted|limited)",
            r"\b(?:bypass|get around|circumvent)\s+(?:filters|restrictions|limitations|rules)",
            r"\blet's\s+(?:try|do)\s+(?:something|this)\s+(?:differently|another way)\s+to\s+(?:avoid|bypass)",
        ]

        for pattern in circumvention_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return True, "Potential attempt to circumvent content filters detected in conversation context"

        # Check for escalating harmful content
        harmful_count = 0
        for msg in context_messages:
            filtered, _ = self.filter_content(msg["content"])
            if filtered:
                harmful_count += 1

        if harmful_count >= 3:  # If there are multiple filtered messages in context
            return True, "Multiple policy violations detected in conversation context"

        return False, ""

    def filter_content(self, text: str) -> Tuple[bool, str]:
        """Apply all content filters to the text."""
        if not config.content_filter_enabled:
            return False, ""

        # Check language support
        if not self.is_language_supported(text):
            return True, "Language not supported"

        # Apply various filters
        filtered, reason = self.contains_forbidden_words(text)
        if filtered:
            return filtered, reason

        filtered, reason = self.contains_forbidden_patterns(text)
        if filtered:
            return filtered, reason

        filtered, reason = self.contains_profanity(text)
        if filtered:
            return filtered, reason

        filtered, reason = self.analyze_intent(text)
        if filtered:
            return filtered, reason

        return False, ""

# Create a global content filter instance
content_filter = ContentFilter()
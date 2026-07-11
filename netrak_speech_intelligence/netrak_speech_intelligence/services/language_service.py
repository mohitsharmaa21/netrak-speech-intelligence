"""Netrak Speech Intelligence - Language Identification"""
import logging
import re
from typing import Dict

logger = logging.getLogger(__name__)


class LanguageService:
    """Language identification using Whisper as primary signal"""
    
    # Language code mapping
    LANGUAGE_NAMES = {
        "hi": "Hindi",
        "en": "English",
        "ur": "Urdu",
        "pa": "Punjabi",
        "bn": "Bengali",
        "gu": "Gujarati",
        "mr": "Marathi",
        "ta": "Tamil",
        "te": "Telugu",
        "kn": "Kannada",
        "ml": "Malayalam",
    }
    
    # Romanized Hindi/Hinglish markers
    HINGLISH_MARKERS = [
        "aap", "aapka", "aapke", "hai", "hain", "hoon",
        "karna", "karo", "kijiye", "paisa", "paise", "bhejo",
        "turant", "nahi", "giraftar", "khata", "rupaye",
        "main", "mein", "se", "bol", "raha", "hoon"
    ]
    
    def identify(self, language_code: str, transcript: str, probability: float = None) -> Dict[str, any]:
        """
        Identify language from Whisper output
        
        Args:
            language_code: Language code from Whisper
            transcript: Transcript text
            probability: Language probability from Whisper (if available)
        
        Returns:
            Dict containing:
                - code: Language code
                - name: Language name
                - confidence: Confidence score
                - code_switch_detected: Whether code-switching detected (optional)
        """
        # Get language name
        language_name = self.LANGUAGE_NAMES.get(language_code, language_code.upper())
        
        # Use Whisper probability if available, else default
        confidence = probability if probability is not None else 0.85
        
        result = {
            "code": language_code,
            "name": language_name,
            "confidence": confidence
        }
        
        # Detect code-switching (Hinglish heuristic)
        if language_code in ["hi", "en"]:
            code_switch = self._detect_code_switching(transcript)
            if code_switch:
                result["code_switch_detected"] = True
        
        logger.info(f"Language identified: {language_name} ({language_code}), confidence={confidence:.4f}")
        
        return result
    
    def _detect_code_switching(self, transcript: str) -> bool:
        """
        Detect Hindi-English code-switching (Hinglish)
        
        Args:
            transcript: Transcript text
        
        Returns:
            True if code-switching detected
        """
        try:
            transcript_lower = transcript.lower()
            
            # Count Hinglish markers
            marker_count = sum(1 for marker in self.HINGLISH_MARKERS if marker in transcript_lower)
            
            # If multiple Romanized Hindi words present alongside English
            if marker_count >= 3:
                logger.debug(f"Code-switching detected: {marker_count} Hinglish markers found")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Code-switch detection failed: {e}")
            return False
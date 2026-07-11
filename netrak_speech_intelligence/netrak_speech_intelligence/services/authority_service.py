"""Netrak Speech Intelligence - Authority Impersonation Detection"""
import json
import logging
import re
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class AuthorityService:
    """Authority impersonation detection service"""
    
    # Self-representation patterns
    SELF_REP_PATTERNS_EN = [
        r"i am from (the |an? )?(cbi|police|customs|court|rbi)",
        r"this is (the |an? )?(cbi|police|customs|court|rbi)",
        r"i am an? (cbi|police|customs|court|officer|investigat)",
        r"calling from (the )?(cbi|cyber|police|customs|court|rbi)",
        r"we are from (the )?(cbi|police|customs|court|rbi)",
        r"i am (the |an? )?(officer|investigat)",
    ]
    
    SELF_REP_PATTERNS_HI = [
        r"main (cbi|police|cyber|customs) se bol raha",
        r"hum (cbi|police|cyber|customs) se (hain|hai)",
        r"main (police )?officer (hoon|bol raha)",
        r"(cyber|crime) (cell|branch) se bol raha",
        r"customs se call (hai|ho rahi)",
        r"main officer (hoon|bol raha)",
        r"hum investigation team se (hain|hai)",
    ]
    
    def __init__(self, authorities_path: Path):
        """
        Initialize authority service
        
        Args:
            authorities_path: Path to authorities.json
        """
        self.authorities_path = authorities_path
        self.authorities = self._load_authorities()
        logger.info(f"Loaded {len(self.authorities)} authorities")
    
    def _load_authorities(self) -> List[str]:
        """
        Load authorities from JSON
        
        Returns:
            List of authority names
        """
        try:
            with open(self.authorities_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("authorities", [])
        except Exception as e:
            logger.error(f"Failed to load authorities: {e}")
            return []
    
    def detect(self, transcript: str, category_counts: Dict[str, int]) -> Dict[str, any]:
        """
        Detect authority impersonation
        
        Args:
            transcript: Transcript text
            category_counts: Keyword category counts
        
        Returns:
            Dict containing:
                - detected: Whether impersonation detected
                - authorities: List of detected authorities
                - confidence: Confidence score
        """
        transcript_lower = transcript.lower()
        
        # Detect authorities mentioned
        detected_authorities = self._detect_authorities(transcript_lower)
        
        if not detected_authorities:
            return {
                "detected": False,
                "authorities": [],
                "confidence": 0.0
            }
        
        # Check for self-representation patterns
        has_self_rep = self._detect_self_representation(transcript_lower)
        
        if not has_self_rep:
            # Authority mentioned but no self-representation
            return {
                "detected": False,
                "authorities": detected_authorities,
                "confidence": 0.0
            }
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            detected_authorities,
            has_self_rep,
            category_counts
        )
        
        logger.info(
            f"Authority impersonation detected: {detected_authorities}, "
            f"confidence={confidence:.4f}"
        )
        
        return {
            "detected": True,
            "authorities": detected_authorities,
            "confidence": confidence
        }
    
    def _detect_authorities(self, text: str) -> List[str]:
        """
        Detect which authorities are mentioned
        
        Args:
            text: Text to search
        
        Returns:
            List of detected authorities
        """
        detected = []
        
        for authority in self.authorities:
            authority_lower = authority.lower()
            if authority_lower in text:
                detected.append(authority)
        
        return detected
    
    def _detect_self_representation(self, text: str) -> bool:
        """
        Detect self-representation patterns
        
        Args:
            text: Text to search
        
        Returns:
            True if self-representation pattern found
        """
        # Check English patterns
        for pattern in self.SELF_REP_PATTERNS_EN:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check Hindi/Hinglish patterns
        for pattern in self.SELF_REP_PATTERNS_HI:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_confidence(self, authorities: List[str], has_self_rep: bool, category_counts: Dict[str, int]) -> float:
        """
        Calculate authority impersonation confidence
        
        Args:
            authorities: Detected authorities
            has_self_rep: Whether self-representation detected
            category_counts: Keyword category counts
        
        Returns:
            Confidence score [0, 1]
        """
        confidence = 0.0
        
        # Base confidence for self-representation
        if has_self_rep:
            confidence += 0.40
        
        # Authority mentioned
        if authorities:
            confidence += 0.30
        
        # Threat/legal vocabulary
        if category_counts.get("threat", 0) > 0:
            confidence += 0.20
        
        # Urgency
        if category_counts.get("urgency", 0) > 0:
            confidence += 0.10
        
        return min(confidence, 1.0)
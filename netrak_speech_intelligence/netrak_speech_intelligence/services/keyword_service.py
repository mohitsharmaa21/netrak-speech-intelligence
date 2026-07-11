"""Netrak Speech Intelligence - Scam Keyword Detection"""
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class KeywordService:
    """Scam keyword detection service"""
    
    def __init__(self, keywords_path: Path):
        """
        Initialize keyword service
        
        Args:
            keywords_path: Path to scam_keywords.json
        """
        self.keywords_path = keywords_path
        self.keywords_by_category = self._load_keywords()
        logger.info(f"Loaded {sum(len(v) for v in self.keywords_by_category.values())} keywords")
    
    def _load_keywords(self) -> Dict[str, List[str]]:
        """
        Load keywords from JSON
        
        Returns:
            Dict mapping category to list of keywords
        """
        try:
            with open(self.keywords_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Failed to load keywords: {e}")
            return {}
    
    def detect(self, transcript: str) -> tuple:
        """
        Detect scam keywords in transcript
        
        Args:
            transcript: Transcript text
        
        Returns:
            Tuple of (detected_keywords, category_counts)
                - detected_keywords: List of detected keyword dicts
                - category_counts: Dict mapping category to hit count
        """
        transcript_lower = transcript.lower()
        detected_keywords = []
        detected_set: Set[str] = set()  # For deduplication
        category_counts = defaultdict(int)
        
        for category, keywords in self.keywords_by_category.items():
            for keyword in keywords:
                if self._match_keyword(keyword, transcript_lower):
                    # Deduplicate
                    if keyword not in detected_set:
                        detected_keywords.append({
                            "keyword": keyword,
                            "category": category
                        })
                        detected_set.add(keyword)
                        category_counts[category] += 1
        
        logger.info(f"Detected {len(detected_keywords)} keywords across {len(category_counts)} categories")
        
        return detected_keywords, dict(category_counts)
    
    def _match_keyword(self, keyword: str, text: str) -> bool:
        """
        Match keyword in text with word boundaries
        
        Args:
            keyword: Keyword to match
            text: Text to search
        
        Returns:
            True if keyword found
        """
        keyword_lower = keyword.lower()
        
        # For short keywords that might be substrings (e.g., "ed")
        # Use word boundary matching
        if len(keyword_lower) <= 3:
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            return re.search(pattern, text) is not None
        else:
            # For longer keywords/phrases, simple substring match
            return keyword_lower in text
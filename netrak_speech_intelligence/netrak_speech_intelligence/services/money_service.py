"""Netrak Speech Intelligence - Money Request Detection"""
import json
import logging
import re
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class MoneyService:
    """Money request detection service"""
    
    # Money request patterns
    REQUEST_PATTERNS_EN = [
        r"transfer (now|immediately|money|rupees|amount)",
        r"send (money|payment|rupees|amount)",
        r"make (payment|deposit|transfer)",
        r"(pay|deposit) (amount|money|rupees|immediately)",
        r"(immediate|urgent) (payment|transfer|deposit)",
    ]
    
    REQUEST_PATTERNS_HI = [
        r"transfer (karo|kijiye|bhejo)",
        r"(paise|paisa|rupaye) (bhejo|transfer|jama)",
        r"payment (karo|kijiye)",
        r"(jama|deposit) karo",
        r"turant (transfer|payment|bhejo)",
    ]
    
    # Amount extraction patterns
    AMOUNT_PATTERNS = [
        r"[₹\$]\s*([\d,]+)",  # ₹50,000 or $1000
        r"Rs\.?\s*([\d,]+)",  # Rs. 50000
        r"INR\s*([\d,]+)",  # INR 50000
        r"([\d,]+)\s*(rupees|rupaye)",  # 50000 rupees
    ]
    
    # Hindi number words (limited)
    HINDI_NUMBERS = {
        "das": "10",
        "bees": "20",
        "pachaas": "50",
        "sau": "100",
        "hazaar": "1000",
        "lakh": "100000",
        "ek hazaar": "1000",
        "das hazaar": "10000",
        "bees hazaar": "20000",
        "pachaas hazaar": "50000",
        "ek lakh": "100000",
        "do lakh": "200000",
        "paanch lakh": "500000",
    }
    
    def __init__(self, payment_patterns_path: Path):
        """
        Initialize money service
        
        Args:
            payment_patterns_path: Path to payment_patterns.json
        """
        self.payment_patterns_path = payment_patterns_path
        self.payment_patterns = self._load_patterns()
        logger.info("Money service initialized")
    
    def _load_patterns(self) -> Dict:
        """
        Load payment patterns from JSON
        
        Returns:
            Payment patterns dict
        """
        try:
            with open(self.payment_patterns_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Failed to load payment patterns: {e}")
            return {"payment_methods": [], "platforms": []}
    
    def detect(self, transcript: str) -> Dict[str, any]:
        """
        Detect money request
        
        Args:
            transcript: Transcript text
        
        Returns:
            Dict containing:
                - detected: Whether money request detected
                - payment_methods: List of payment methods
                - amounts: List of detected amounts
                - confidence: Confidence score
        """
        transcript_lower = transcript.lower()
        
        # Detect request patterns
        has_request = self._detect_request_pattern(transcript_lower)
        
        if not has_request:
            return {
                "detected": False,
                "payment_methods": [],
                "amounts": [],
                "confidence": 0.0
            }
        
        # Detect payment methods
        payment_methods = self._detect_payment_methods(transcript_lower)
        
        # Extract amounts
        amounts = self._extract_amounts(transcript_lower)
        
        # Calculate confidence
        confidence = self._calculate_confidence(has_request, payment_methods, amounts)
        
        logger.info(
            f"Money request detected: methods={payment_methods}, "
            f"amounts={amounts}, confidence={confidence:.4f}"
        )
        
        return {
            "detected": True,
            "payment_methods": payment_methods,
            "amounts": amounts,
            "confidence": confidence
        }
    
    def _detect_request_pattern(self, text: str) -> bool:
        """
        Detect money request patterns
        
        Args:
            text: Text to search
        
        Returns:
            True if request pattern found
        """
        # English patterns
        for pattern in self.REQUEST_PATTERNS_EN:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Hindi/Hinglish patterns
        for pattern in self.REQUEST_PATTERNS_HI:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _detect_payment_methods(self, text: str) -> List[str]:
        """
        Detect payment methods
        
        Args:
            text: Text to search
        
        Returns:
            List of detected payment methods
        """
        methods = []
        
        for method in self.payment_patterns.get("payment_methods", []):
            method_lower = method.lower()
            if method_lower in text:
                methods.append(method)
        
        # Default to bank_transfer if no specific method found
        if not methods:
            if any(word in text for word in ["transfer", "bhejo", "jama"]):
                methods.append("bank_transfer")
        
        return methods
    
    def _extract_amounts(self, text: str) -> List[str]:
        """
        Extract money amounts from text
        
        Args:
            text: Text to search
        
        Returns:
            List of detected amounts
        """
        amounts = []
        
        # Extract numeric amounts
        for pattern in self.AMOUNT_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean amount
                if isinstance(match, tuple):
                    amount = match[0]
                else:
                    amount = match
                amount = amount.replace(',', '')
                if amount.isdigit():
                    amounts.append(amount)
        
        # Extract Hindi number words
        for hindi_num, value in self.HINDI_NUMBERS.items():
            if hindi_num in text:
                amounts.append(value)
        
        return list(set(amounts))  # Deduplicate
    
    def _calculate_confidence(self, has_request: bool, payment_methods: List[str], amounts: List[str]) -> float:
        """
        Calculate money request confidence
        
        Args:
            has_request: Whether request pattern detected
            payment_methods: Detected payment methods
            amounts: Detected amounts
        
        Returns:
            Confidence score [0, 1]
        """
        confidence = 0.0
        
        # Request pattern
        if has_request:
            confidence += 0.50
        
        # Payment method
        if payment_methods:
            confidence += 0.25
        
        # Amounts
        if amounts:
            confidence += 0.25
        
        return min(confidence, 1.0)
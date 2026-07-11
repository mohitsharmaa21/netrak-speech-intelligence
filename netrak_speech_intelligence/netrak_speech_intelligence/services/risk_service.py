"""Netrak Speech Intelligence - Risk Scoring Engine"""
import logging
from typing import Dict, List, Literal

logger = logging.getLogger(__name__)


class RiskService:
    """Explainable risk scoring engine"""
    
    def __init__(
        self,
        weight_authority: float = 0.25,
        weight_money_request: float = 0.25,
        weight_threat: float = 0.15,
        weight_urgency: float = 0.10,
        weight_digital_arrest: float = 0.10,
        weight_secrecy: float = 0.05,
        weight_remote_access: float = 0.05,
        weight_ai_voice: float = 0.05,
    ):
        """
        Initialize risk scoring service
        
        Args:
            weight_*: Weight for each risk factor
        """
        self.weight_authority = weight_authority
        self.weight_money_request = weight_money_request
        self.weight_threat = weight_threat
        self.weight_urgency = weight_urgency
        self.weight_digital_arrest = weight_digital_arrest
        self.weight_secrecy = weight_secrecy
        self.weight_remote_access = weight_remote_access
        self.weight_ai_voice = weight_ai_voice
        
        logger.info("Risk scoring service initialized")
    
    def calculate_risk(
        self,
        authority_result: Dict,
        money_result: Dict,
        category_counts: Dict[str, int],
        ai_voice_probability: float = None
    ) -> Dict[str, any]:
        """
        Calculate risk score
        
        Args:
            authority_result: Authority impersonation detection result
            money_result: Money request detection result
            category_counts: Keyword category counts
            ai_voice_probability: AI voice probability (optional)
        
        Returns:
            Dict containing:
                - score: Risk score [0, 1]
                - level: 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'
                - reasons: List of human-readable reasons
        """
        score = 0.0
        reasons = []
        
        # Authority impersonation
        if authority_result.get("detected"):
            score += self.weight_authority
            authorities = authority_result.get("authorities", [])
            authorities_str = ", ".join(authorities)
            reasons.append(f"Authority impersonation detected: {authorities_str}")
        
        # Money request
        if money_result.get("detected"):
            score += self.weight_money_request
            amounts = money_result.get("amounts", [])
            if amounts:
                amounts_str = ", ".join(amounts)
                reasons.append(f"Money transfer request detected (amounts: {amounts_str})")
            else:
                reasons.append("Money transfer request detected")
        
        # Threat category
        if category_counts.get("threat", 0) > 0:
            score += self.weight_threat
            reasons.append("Threat or arrest language detected")
        
        # Urgency category
        if category_counts.get("urgency", 0) > 0:
            score += self.weight_urgency
            reasons.append("Urgency language detected")
        
        # Digital arrest category
        if category_counts.get("digital_arrest", 0) > 0:
            score += self.weight_digital_arrest
            reasons.append("Digital arrest scam indicators detected")
        
        # Secrecy category
        if category_counts.get("secrecy", 0) > 0:
            score += self.weight_secrecy
            reasons.append("Secrecy instruction detected")
        
        # Remote access category
        if category_counts.get("remote_access", 0) > 0:
            score += self.weight_remote_access
            reasons.append("Remote access software request detected")
        
        # AI voice
        if ai_voice_probability is not None and ai_voice_probability >= 0.70:
            ai_contribution = ai_voice_probability * self.weight_ai_voice
            score += ai_contribution
            reasons.append(f"Possible AI-generated voice detected (probability: {ai_voice_probability:.2f})")
        
        # Cap at 1.0
        score = min(score, 1.0)
        
        # Determine risk level
        level = self._determine_level(score)
        
        logger.info(f"Risk calculated: score={score:.4f}, level={level}, factors={len(reasons)}")
        
        return {
            "score": score,
            "level": level,
            "reasons": reasons
        }
    
    def _determine_level(self, score: float) -> Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        """
        Determine risk level from score
        
        Args:
            score: Risk score [0, 1]
        
        Returns:
            Risk level
        """
        if score <= 0.29:
            return "LOW"
        elif score <= 0.59:
            return "MEDIUM"
        elif score <= 0.79:
            return "HIGH"
        else:
            return "CRITICAL"
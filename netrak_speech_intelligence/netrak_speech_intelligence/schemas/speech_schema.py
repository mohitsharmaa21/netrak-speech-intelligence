"""Netrak Speech Intelligence - Pydantic API Schemas"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class LanguageResult(BaseModel):
    """Language identification result"""
    code: str = Field(..., description="Language code (e.g., 'hi', 'en')")
    name: str = Field(..., description="Language name (e.g., 'Hindi', 'English')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0, 1]")
    code_switch_detected: Optional[bool] = Field(None, description="Whether code-switching detected")


class AIVoiceResult(BaseModel):
    """AI voice / deepfake detection result"""
    probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI voice probability [0, 1]")
    prediction: Literal["likely_ai", "likely_human", "uncertain", "unavailable"] = Field(
        ..., description="Prediction category"
    )
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score [0, 1]")


class ScamKeyword(BaseModel):
    """Detected scam keyword"""
    keyword: str = Field(..., description="Detected keyword")
    category: str = Field(..., description="Keyword category")


class AuthorityResult(BaseModel):
    """Authority impersonation detection result"""
    detected: bool = Field(..., description="Whether impersonation detected")
    authorities: List[str] = Field(default_factory=list, description="Detected authorities")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0, 1]")


class MoneyRequestResult(BaseModel):
    """Money request detection result"""
    detected: bool = Field(..., description="Whether money request detected")
    payment_methods: List[str] = Field(default_factory=list, description="Detected payment methods")
    amounts: List[str] = Field(default_factory=list, description="Detected amounts")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0, 1]")


class RiskResult(BaseModel):
    """Risk assessment result"""
    score: float = Field(..., ge=0.0, le=1.0, description="Risk score [0, 1]")
    level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(..., description="Risk level")
    reasons: List[str] = Field(..., description="Human-readable risk factors")


class SpeechAnalysisResponse(BaseModel):
    """Complete speech analysis response"""
    request_id: str = Field(..., description="Unique request ID")
    model_version: str = Field(..., description="Model version")
    transcript: str = Field(..., description="Transcribed text")
    detected_language: LanguageResult = Field(..., description="Language identification result")
    ai_voice: AIVoiceResult = Field(..., description="AI voice detection result")
    scam_keywords: List[ScamKeyword] = Field(..., description="Detected scam keywords")
    authority_impersonation: AuthorityResult = Field(..., description="Authority impersonation result")
    money_request: MoneyRequestResult = Field(..., description="Money request detection result")
    risk: RiskResult = Field(..., description="Risk assessment")
    processing_time_ms: int = Field(..., ge=0, description="Processing time in milliseconds")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    request_id: Optional[str] = Field(None, description="Request ID if available")
"""Netrak Speech Intelligence - Settings and Configuration"""
import os
from pathlib import Path
from typing import List, Literal
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings for Netrak Speech Intelligence Service"""
    
    # Service metadata
    service_name: str = "netrak-speech-intelligence"
    service_version: str = "1.0.0"
    model_version: str = "speech-intelligence-v1.0.0"
    
    # Audio processing
    max_audio_size_mb: int = Field(default=25, description="Maximum audio upload size in MB")
    target_sample_rate: int = Field(default=16000, description="Target sample rate for audio preprocessing")
    min_audio_duration_sec: float = Field(default=0.5, description="Minimum audio duration in seconds")
    max_audio_duration_sec: float = Field(default=600, description="Maximum audio duration in seconds (10 min)")
    silence_threshold_rms: float = Field(default=0.01, description="RMS threshold for silence detection")
    
    # Supported audio formats
    supported_audio_formats: List[str] = ["wav", "mp3", "m4a", "flac", "ogg"]
    
    # Model configurations
    whisper_model_name: str = Field(default="base", description="Whisper model: tiny, base, small, medium, large")
    voice_spoof_model_id: str = Field(
        default="Gustking/wav2vec2-large-xlsr-deepfake-audio-classification",
        description="HuggingFace model ID for voice spoof detection"
    )
    
    # Voice spoof detector settings
    voice_chunk_duration_sec: float = Field(default=5.0, description="Chunk duration for voice spoof detection")
    voice_spoof_threshold_likely_ai: float = Field(default=0.70, description="Threshold for likely AI")
    voice_spoof_threshold_likely_human: float = Field(default=0.30, description="Threshold for likely human")
    
    # Risk scoring weights
    risk_weight_authority: float = 0.25
    risk_weight_money_request: float = 0.25
    risk_weight_threat: float = 0.15
    risk_weight_urgency: float = 0.10
    risk_weight_digital_arrest: float = 0.10
    risk_weight_secrecy: float = 0.05
    risk_weight_remote_access: float = 0.05
    risk_weight_ai_voice: float = 0.05
    
    # Risk level thresholds
    risk_threshold_low: float = 0.29
    risk_threshold_medium: float = 0.59
    risk_threshold_high: float = 0.79
    # Above 0.79 is CRITICAL
    
    # Compute settings
    device: Literal["auto", "cuda", "cpu"] = Field(
        default="auto",
        description="Device for model inference. 'auto' will use CUDA if available."
    )
    fp16: bool = Field(
        default=True,
        description="Use FP16 precision for Whisper (only when CUDA available)"
    )
    
    # API settings
    cors_origins: List[str] = Field(
        default=["*"],
        description="CORS allowed origins. Use specific origins in production."
    )
    
    # Paths
    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent
    
    @property
    def resources_dir(self) -> Path:
        return self.project_root / "resources"
    
    @property
    def scam_keywords_path(self) -> Path:
        return self.resources_dir / "scam_keywords.json"
    
    @property
    def authorities_path(self) -> Path:
        return self.resources_dir / "authorities.json"
    
    @property
    def payment_patterns_path(self) -> Path:
        return self.resources_dir / "payment_patterns.json"
    
    class Config:
        env_prefix = "NETRAK_"


# Singleton instance
_settings: Settings = None


def get_settings() -> Settings:
    """Get singleton settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
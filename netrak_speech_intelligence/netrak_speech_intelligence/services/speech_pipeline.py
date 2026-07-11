"""Netrak Speech Intelligence - Main Pipeline Orchestrator"""
import logging
import time
import uuid
import tempfile
import os
from typing import Dict

from ..config import Settings
from ..models import WhisperSpeechToText, VoiceSpoofDetector
from .audio_preprocessor import AudioPreprocessor
from .language_service import LanguageService
from .keyword_service import KeywordService
from .authority_service import AuthorityService
from .money_service import MoneyService
from .risk_service import RiskService

logger = logging.getLogger(__name__)


class SpeechIntelligencePipeline:
    """Main speech intelligence pipeline orchestrator"""
    
    def __init__(self, settings: Settings):
        """
        Initialize pipeline
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        
        logger.info("Initializing Netrak Speech Intelligence Pipeline")
        
        # Initialize audio preprocessor
        self.audio_preprocessor = AudioPreprocessor(
            target_sample_rate=settings.target_sample_rate,
            max_size_mb=settings.max_audio_size_mb,
            min_duration_sec=settings.min_audio_duration_sec,
            max_duration_sec=settings.max_audio_duration_sec,
            silence_threshold=settings.silence_threshold_rms,
            supported_formats=settings.supported_audio_formats
        )
        
        # Initialize Whisper speech-to-text
        self.whisper = WhisperSpeechToText(
            model_name=settings.whisper_model_name,
            device=settings.device,
            fp16=settings.fp16
        )
        
        # Initialize voice spoof detector
        try:
            self.voice_detector = VoiceSpoofDetector(
                model_id=settings.voice_spoof_model_id,
                device=settings.device,
                chunk_duration=settings.voice_chunk_duration_sec
            )
            self.voice_detector_available = True
        except Exception as e:
            logger.warning(f"Voice spoof detector failed to initialize: {e}")
            self.voice_detector_available = False
        
        # Initialize services
        self.language_service = LanguageService()
        self.keyword_service = KeywordService(settings.scam_keywords_path)
        self.authority_service = AuthorityService(settings.authorities_path)
        self.money_service = MoneyService(settings.payment_patterns_path)
        self.risk_service = RiskService(
            weight_authority=settings.risk_weight_authority,
            weight_money_request=settings.risk_weight_money_request,
            weight_threat=settings.risk_weight_threat,
            weight_urgency=settings.risk_weight_urgency,
            weight_digital_arrest=settings.risk_weight_digital_arrest,
            weight_secrecy=settings.risk_weight_secrecy,
            weight_remote_access=settings.risk_weight_remote_access,
            weight_ai_voice=settings.risk_weight_ai_voice
        )
        
        logger.info("Pipeline initialized successfully")
    
    def analyze(self, audio_path: str) -> Dict:
        """
        Analyze audio file for scam detection
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Complete analysis result dict
        """
        request_id = str(uuid.uuid4())
        start_time = time.time()
        temp_file_path = None
        
        try:
            logger.info(f"Starting analysis for request {request_id}")
            
            # 1. Preprocess audio
            logger.info("Step 1: Audio preprocessing")
            audio_data = self.audio_preprocessor.process(audio_path)
            
            # Save to temp file for model inference
            temp_file_path = self.audio_preprocessor.save_temp(audio_data)
            
            # 2. Speech-to-text transcription
            logger.info("Step 2: Speech-to-text transcription")
            transcription_result = self.whisper.transcribe(temp_file_path)
            transcript = transcription_result["transcript"]
            whisper_language = transcription_result["detected_language_code"]
            
            if not transcript or len(transcript.strip()) == 0:
                raise ValueError("Transcription resulted in empty text")
            
            logger.info(f"Transcript: {transcript[:100]}...")
            
            # 3. Language identification
            logger.info("Step 3: Language identification")
            language_result = self.language_service.identify(
                language_code=whisper_language,
                transcript=transcript,
                probability=None  # Could use detect_language for probability
            )
            
            # 4. AI voice detection (optional, may fail)
            logger.info("Step 4: AI voice detection")
            if self.voice_detector_available:
                try:
                    ai_voice_result = self.voice_detector.detect(
                        temp_file_path,
                        sample_rate=audio_data.sample_rate
                    )
                except Exception as e:
                    logger.warning(f"Voice detection failed: {e}")
                    ai_voice_result = {
                        "probability": None,
                        "prediction": "unavailable",
                        "confidence": None
                    }
            else:
                ai_voice_result = {
                    "probability": None,
                    "prediction": "unavailable",
                    "confidence": None
                }
            
            # 5. Keyword detection
            logger.info("Step 5: Scam keyword detection")
            detected_keywords, category_counts = self.keyword_service.detect(transcript)
            
            # 6. Authority impersonation detection
            logger.info("Step 6: Authority impersonation detection")
            authority_result = self.authority_service.detect(transcript, category_counts)
            
            # 7. Money request detection
            logger.info("Step 7: Money request detection")
            money_result = self.money_service.detect(transcript)
            
            # 8. Risk scoring
            logger.info("Step 8: Risk scoring")
            risk_result = self.risk_service.calculate_risk(
                authority_result=authority_result,
                money_result=money_result,
                category_counts=category_counts,
                ai_voice_probability=ai_voice_result.get("probability")
            )
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"Analysis complete for request {request_id}: "
                f"risk={risk_result['level']}, time={processing_time_ms}ms"
            )
            
            # Build response
            return {
                "request_id": request_id,
                "model_version": self.settings.model_version,
                "transcript": transcript,
                "detected_language": language_result,
                "ai_voice": ai_voice_result,
                "scam_keywords": detected_keywords,
                "authority_impersonation": authority_result,
                "money_request": money_result,
                "risk": risk_result,
                "processing_time_ms": processing_time_ms
            }
            
        finally:
            # Cleanup temp file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temp file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file: {e}")
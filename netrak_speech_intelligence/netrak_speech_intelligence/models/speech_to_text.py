"""Netrak Speech Intelligence - Speech-to-Text using OpenAI Whisper"""
import logging
import re
from typing import Dict, Optional

import torch
import whisper
from whisper import Whisper

logger = logging.getLogger(__name__)


class WhisperSpeechToText:
    """OpenAI Whisper-based speech-to-text transcription"""
    
    def __init__(self, model_name: str = "base", device: str = "auto", fp16: bool = True):
        """
        Initialize Whisper model
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            device: Device for inference ('auto', 'cuda', 'cpu')
            fp16: Use FP16 precision (only when CUDA available)
        """
        self.model_name = model_name
        
        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # FP16 only works on CUDA
        self.fp16 = fp16 and self.device == "cuda"
        
        logger.info(f"Loading Whisper model '{model_name}' on device '{self.device}' (fp16={self.fp16})")
        
        try:
            self.model: Whisper = whisper.load_model(model_name, device=self.device)
            logger.info(f"Whisper model '{model_name}' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def transcribe(self, audio_path: str) -> Dict[str, any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Dict containing:
                - transcript: Cleaned transcript text
                - detected_language_code: Whisper-detected language code
                - detected_language_probability: Language detection confidence
        """
        try:
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Run Whisper transcription
            result = self.model.transcribe(
                audio_path,
                task="transcribe",  # Do NOT translate to English
                fp16=self.fp16,
                language=None,  # Auto-detect language
            )
            
            # Extract results
            raw_transcript = result.get("text", "")
            detected_language = result.get("language", "unknown")
            
            # Clean transcript
            transcript = self._clean_transcript(raw_transcript)
            
            logger.info(f"Transcription complete. Language: {detected_language}, Length: {len(transcript)} chars")
            
            return {
                "transcript": transcript,
                "detected_language_code": detected_language,
                "detected_language_probability": None  # Whisper doesn't expose this in simple API
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            raise RuntimeError(f"Speech-to-text transcription failed: {e}")
    
    def detect_language(self, audio_path: str) -> Dict[str, any]:
        """
        Detect language from audio (alternative to transcription)
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Dict containing:
                - detected_language_code: Language code
                - detected_language_probability: Probability score
        """
        try:
            # Load audio
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            
            # Make log-Mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            # Detect language
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            probability = probs[detected_language]
            
            logger.info(f"Language detected: {detected_language} (prob: {probability:.4f})")
            
            return {
                "detected_language_code": detected_language,
                "detected_language_probability": float(probability)
            }
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}", exc_info=True)
            return {
                "detected_language_code": "unknown",
                "detected_language_probability": 0.0
            }
    
    @staticmethod
    def _clean_transcript(text: str) -> str:
        """
        Clean transcript text
        
        Args:
            text: Raw transcript
        
        Returns:
            Cleaned transcript
        """
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Collapse repeated whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Do NOT remove punctuation or numbers - they are important for fraud detection
        return text
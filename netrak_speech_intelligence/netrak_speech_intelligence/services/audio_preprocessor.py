"""Netrak Speech Intelligence - Audio Preprocessing"""
import logging
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import numpy as np
import librosa
import soundfile as sf

logger = logging.getLogger(__name__)


class AudioValidationError(Exception):
    """Raised when audio validation fails"""
    pass


class UnsupportedFormatError(AudioValidationError):
    """Raised when audio format is not supported"""
    pass


class AudioTooLargeError(AudioValidationError):
    """Raised when audio file is too large"""
    pass


class AudioTooShortError(AudioValidationError):
    """Raised when audio is too short"""
    pass


class AudioTooLongError(AudioValidationError):
    """Raised when audio is too long"""
    pass


class AudioSilentError(AudioValidationError):
    """Raised when audio is near-silent"""
    pass


@dataclass
class AudioData:
    """Preprocessed audio data"""
    waveform: np.ndarray
    sample_rate: int
    duration_seconds: float
    rms_energy: float
    temp_path: Optional[str] = None


class AudioPreprocessor:
    """Audio validation and preprocessing"""
    
    def __init__(
        self,
        target_sample_rate: int = 16000,
        max_size_mb: int = 25,
        min_duration_sec: float = 0.5,
        max_duration_sec: float = 600,
        silence_threshold: float = 0.01,
        supported_formats: Optional[list] = None
    ):
        """
        Initialize audio preprocessor
        
        Args:
            target_sample_rate: Target sample rate for preprocessing
            max_size_mb: Maximum file size in MB
            min_duration_sec: Minimum audio duration
            max_duration_sec: Maximum audio duration
            silence_threshold: RMS threshold for silence detection
            supported_formats: List of supported file extensions
        """
        self.target_sample_rate = target_sample_rate
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.min_duration_sec = min_duration_sec
        self.max_duration_sec = max_duration_sec
        self.silence_threshold = silence_threshold
        self.supported_formats = supported_formats or ["wav", "mp3", "m4a", "flac", "ogg"]
    
    def process(self, file_path: str) -> AudioData:
        """
        Validate and preprocess audio file
        
        Args:
            file_path: Path to audio file
        
        Returns:
            AudioData object
        
        Raises:
            AudioValidationError: If validation fails
        """
        try:
            # Validate format
            self._validate_format(file_path)
            
            # Validate size
            self._validate_size(file_path)
            
            # Load and validate audio
            waveform, sample_rate = self._load_audio(file_path)
            
            # Calculate metrics
            duration = len(waveform) / sample_rate
            rms_energy = float(np.sqrt(np.mean(waveform ** 2)))
            
            # Validate duration
            self._validate_duration(duration)
            
            # Validate not silent
            self._validate_not_silent(rms_energy)
            
            # Convert to target sample rate if needed
            if sample_rate != self.target_sample_rate:
                waveform = librosa.resample(
                    waveform,
                    orig_sr=sample_rate,
                    target_sr=self.target_sample_rate
                )
                sample_rate = self.target_sample_rate
            
            # Normalize
            waveform = self._normalize(waveform)
            
            logger.info(
                f"Audio processed successfully: duration={duration:.2f}s, "
                f"sample_rate={sample_rate}Hz, rms={rms_energy:.4f}"
            )
            
            return AudioData(
                waveform=waveform,
                sample_rate=sample_rate,
                duration_seconds=duration,
                rms_energy=rms_energy,
                temp_path=None
            )
            
        except AudioValidationError:
            raise
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}", exc_info=True)
            raise AudioValidationError(f"Failed to process audio: {e}")
    
    def _validate_format(self, file_path: str):
        """Validate audio format"""
        path = Path(file_path)
        extension = path.suffix.lstrip('.').lower()
        
        if extension not in self.supported_formats:
            raise UnsupportedFormatError(
                f"Unsupported format: {extension}. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )
    
    def _validate_size(self, file_path: str):
        """Validate file size"""
        size = Path(file_path).stat().st_size
        
        if size > self.max_size_bytes:
            size_mb = size / (1024 * 1024)
            max_mb = self.max_size_bytes / (1024 * 1024)
            raise AudioTooLargeError(
                f"Audio file too large: {size_mb:.2f}MB. Maximum allowed: {max_mb:.0f}MB"
            )
    
    def _load_audio(self, file_path: str) -> tuple:
        """
        Load audio file
        
        Returns:
            (waveform, sample_rate)
        
        Raises:
            AudioValidationError: If audio cannot be loaded
        """
        try:
            # Load as mono
            waveform, sample_rate = librosa.load(file_path, sr=None, mono=True)
            return waveform, sample_rate
        except Exception as e:
            raise AudioValidationError(f"Failed to load audio file: {e}")
    
    def _validate_duration(self, duration: float):
        """Validate audio duration"""
        if duration < self.min_duration_sec:
            raise AudioTooShortError(
                f"Audio too short: {duration:.2f}s. Minimum: {self.min_duration_sec}s"
            )
        
        if duration > self.max_duration_sec:
            raise AudioTooLongError(
                f"Audio too long: {duration:.2f}s. Maximum: {self.max_duration_sec}s"
            )
    
    def _validate_not_silent(self, rms_energy: float):
        """Validate audio is not silent"""
        if rms_energy < self.silence_threshold:
            raise AudioSilentError(
                f"Audio appears to be silent or near-silent (RMS: {rms_energy:.6f})"
            )
    
    @staticmethod
    def _normalize(waveform: np.ndarray) -> np.ndarray:
        """
        Normalize waveform
        
        Args:
            waveform: Input waveform
        
        Returns:
            Normalized waveform
        """
        max_val = np.abs(waveform).max()
        
        if max_val > 0:
            return waveform / max_val
        else:
            return waveform
    
    def save_temp(self, audio_data: AudioData) -> str:
        """
        Save audio to temporary file
        
        Args:
            audio_data: AudioData object
        
        Returns:
            Path to temporary file
        """
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            )
            temp_path = temp_file.name
            temp_file.close()
            
            # Save audio
            sf.write(
                temp_path,
                audio_data.waveform,
                audio_data.sample_rate
            )
            
            logger.debug(f"Audio saved to temporary file: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to save temporary audio: {e}")
            raise RuntimeError(f"Failed to save audio to temporary file: {e}")
"""Netrak Speech Intelligence - AI Voice / Deepfake Audio Detection"""
import logging
from typing import Dict, List, Optional, Literal

import torch
import numpy as np
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
import librosa

logger = logging.getLogger(__name__)


class VoiceSpoofDetector:
    """AI voice / audio deepfake detection using pretrained models"""
    
    def __init__(
        self,
        model_id: str = "Gustking/wav2vec2-large-xlsr-deepfake-audio-classification",
        device: str = "auto",
        chunk_duration: float = 5.0
    ):
        """
        Initialize voice spoof detector
        
        Args:
            model_id: HuggingFace model ID
            device: Device for inference ('auto', 'cuda', 'cpu')
            chunk_duration: Duration in seconds for audio chunks
        """
        self.model_id = model_id
        self.chunk_duration = chunk_duration
        
        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"Loading voice spoof detector '{model_id}' on device '{self.device}'")
        
        try:
            # Load model and feature extractor
            self.feature_extractor = AutoFeatureExtractor.from_pretrained(model_id)
            self.model = AutoModelForAudioClassification.from_pretrained(model_id)
            self.model.to(self.device)
            self.model.eval()
            
            # Inspect label mapping
            self.id2label = self.model.config.id2label
            logger.info(f"Model labels: {self.id2label}")
            
            # Determine which label corresponds to spoof/fake/AI
            self.spoof_label_id = self._identify_spoof_label()
            logger.info(f"Spoof label identified: {self.id2label[self.spoof_label_id]}")
            
            logger.info(f"Voice spoof detector loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load voice spoof detector: {e}")
            raise
    
    def _identify_spoof_label(self) -> int:
        """
        Identify which label ID corresponds to spoof/fake/AI
        
        Returns:
            Label ID for spoof class
        """
        # Common patterns for spoof/fake/AI labels
        spoof_patterns = ["spoof", "fake", "ai", "deepfake", "generated", "synthetic"]
        
        for label_id, label_text in self.id2label.items():
            label_lower = label_text.lower()
            if any(pattern in label_lower for pattern in spoof_patterns):
                return label_id
        
        # Fallback: assume LABEL_1 or id=1 is spoof (common convention)
        logger.warning("Could not identify spoof label from patterns. Assuming label_id=1 is spoof.")
        return 1
    
    def detect(self, audio_path: str, sample_rate: int = 16000) -> Dict[str, any]:
        """
        Detect AI-generated voice probability
        
        Args:
            audio_path: Path to audio file
            sample_rate: Sample rate of audio
        
        Returns:
            Dict containing:
                - probability: AI voice probability [0, 1]
                - prediction: 'likely_ai', 'likely_human', or 'uncertain'
                - confidence: Same as probability
                - chunk_count: Number of chunks processed
        """
        try:
            logger.info(f"Detecting AI voice for: {audio_path}")
            
            # Load audio
            waveform, sr = librosa.load(audio_path, sr=sample_rate, mono=True)
            
            # Split into chunks
            chunks = self._split_into_chunks(waveform, sample_rate)
            
            if not chunks:
                logger.warning("No valid chunks for voice spoof detection")
                return self._unavailable_result()
            
            # Process chunks
            chunk_probabilities = []
            for chunk in chunks:
                prob = self._process_chunk(chunk, sample_rate)
                if prob is not None:
                    chunk_probabilities.append(prob)
            
            if not chunk_probabilities:
                logger.warning("No valid predictions from chunks")
                return self._unavailable_result()
            
            # Aggregate: mean probability
            ai_probability = float(np.mean(chunk_probabilities))
            
            # Determine prediction
            if ai_probability >= 0.70:
                prediction = "likely_ai"
            elif ai_probability <= 0.30:
                prediction = "likely_human"
            else:
                prediction = "uncertain"
            
            logger.info(
                f"AI voice detection complete: probability={ai_probability:.4f}, "
                f"prediction={prediction}, chunks={len(chunk_probabilities)}"
            )
            
            return {
                "probability": ai_probability,
                "prediction": prediction,
                "confidence": ai_probability,
                "chunk_count": len(chunk_probabilities)
            }
            
        except Exception as e:
            logger.error(f"AI voice detection failed: {e}", exc_info=True)
            return self._unavailable_result()
    
    def _split_into_chunks(self, waveform: np.ndarray, sample_rate: int) -> List[np.ndarray]:
        """
        Split waveform into chunks
        
        Args:
            waveform: Audio waveform
            sample_rate: Sample rate
        
        Returns:
            List of audio chunks
        """
        chunk_samples = int(self.chunk_duration * sample_rate)
        chunks = []
        
        for start in range(0, len(waveform), chunk_samples):
            chunk = waveform[start:start + chunk_samples]
            
            # Skip chunks that are too short
            if len(chunk) < chunk_samples // 2:
                continue
            
            # Skip near-silent chunks
            rms = np.sqrt(np.mean(chunk ** 2))
            if rms < 0.01:
                continue
            
            chunks.append(chunk)
        
        return chunks
    
    def _process_chunk(self, chunk: np.ndarray, sample_rate: int) -> Optional[float]:
        """
        Process single audio chunk
        
        Args:
            chunk: Audio chunk
            sample_rate: Sample rate
        
        Returns:
            Spoof probability for this chunk
        """
        try:
            # Extract features
            inputs = self.feature_extractor(
                chunk,
                sampling_rate=sample_rate,
                return_tensors="pt",
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
            
            # Get probabilities
            probabilities = torch.nn.functional.softmax(logits, dim=-1)
            
            # Extract spoof probability
            spoof_prob = probabilities[0, self.spoof_label_id].item()
            
            return spoof_prob
            
        except Exception as e:
            logger.warning(f"Failed to process chunk: {e}")
            return None
    
    @staticmethod
    def _unavailable_result() -> Dict[str, any]:
        """
        Return unavailable result when detection fails
        """
        return {
            "probability": None,
            "prediction": "unavailable",
            "confidence": None,
            "chunk_count": 0
        }
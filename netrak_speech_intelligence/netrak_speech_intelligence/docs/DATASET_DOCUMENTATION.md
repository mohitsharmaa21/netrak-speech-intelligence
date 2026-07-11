# Netrak Speech Intelligence - Dataset Documentation

## Overview

No Netrak-specific training was performed for the MVP.
All models use pretrained weights.

## Pretrained Models

### 1. OpenAI Whisper (base)
- **Training Data:** 680,000 hours of multilingual audio
- **Languages:** 99 languages
- **Source:** Web-crawled audio with transcripts
- **License:** MIT
- **Paper:** https://arxiv.org/abs/2212.04356

### 2. Voice Spoof Detector
- **Model:** Gustking/wav2vec2-large-xlsr-deepfake-audio-classification
- **Training Data:** Audio deepfake detection dataset
- **Evaluation:** ASVspoof2019, custom datasets
- **HuggingFace:** https://huggingface.co/Gustking/wav2vec2-large-xlsr-deepfake-audio-classification

## Evaluation Datasets (Recommended)

### For Hindi/English ASR Testing
1. **Google FLEURS**
   - Coverage: Hindi, English, and 100+ languages
   - License: CC-BY-4.0
   - Use: Speech-to-text evaluation

2. **OpenSLR Hindi-English Code-Switch Corpus**
   - Coverage: Hinglish / code-switched speech
   - Use: Hinglish transcription testing

### For Scam Detection Testing
- **Synthetic demo scripts** (provided in project)
- User-generated test audio (legally usable)
- Public scam awareness datasets

## Keyword Resources

Scam keywords compiled from:
- Public scam reports
- Financial fraud advisories (RBI, NPCI)
- Cybercrime awareness campaigns
- Common scam patterns documented online

## No Training Data Collection

This MVP does NOT:
- Collect real scam call audio
- Train models on user data
- Require labeled datasets

All fraud detection logic is rule-based and explainable.

## License Compliance

| Dataset/Model | License | Commercial Use | Attribution |
|---------------|---------|----------------|-------------|
| Whisper | MIT | ✅ Yes | Required |
| Wav2Vec2 Spoof | Check model card | Check | Check |
| FLEURS | CC-BY-4.0 | ✅ Yes | Required |

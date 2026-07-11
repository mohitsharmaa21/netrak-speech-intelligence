# Netrak Speech Intelligence - Model Card

## Model Overview

**Service:** Netrak Speech Intelligence Service
**Version:** v1.0.0 (MVP)
**Purpose:** AI-powered speech analysis for scam detection
**Architecture:** Modular inference pipeline

## Components

### 1. Speech-to-Text
- **Model:** OpenAI Whisper base (multilingual)
- **Parameters:** ~74M
- **Languages:** 99 languages including Hindi, English
- **Sample Rate:** 16 kHz
- **Precision:** FP16 on CUDA, FP32 on CPU

### 2. Voice Spoof Detection
- **Model:** Gustking/wav2vec2-large-xlsr-deepfake-audio-classification
- **Architecture:** Wav2Vec2 Large XLSR
- **Task:** Binary classification (bonafide vs spoof)
- **Chunk Processing:** 5-second chunks, aggregated
- **Reported Performance (from model card):**
  - F1 0.95 on model-source evaluation
  - F1 0.9363 on ASVspoof2019 subset

### 3. Keyword Detection
- **Type:** Rule-based pattern matching
- **Categories:** 12 (authority, threat, urgency, money_request, etc.)
- **Languages:** English, Hindi Unicode, Romanized Hindi

### 4. Authority Impersonation Detection
- **Type:** Pattern-based with confidence scoring
- **Patterns:** Self-representation detection (English + Hinglish)
- **Confidence:** Deterministic weighted formula

### 5. Money Request Detection
- **Type:** Pattern-based with amount extraction
- **Amount Extraction:** Numeric + limited Hindi number words
- **Payment Methods:** UPI, bank transfer, NEFT, RTGS, etc.

### 6. Risk Scoring
- **Type:** Explainable weighted scoring
- **Range:** [0.0, 1.0]
- **Weights:** Documented and configurable

## Input Requirements

- **Formats:** WAV, MP3, M4A, FLAC, OGG
- **Max Size:** 25 MB
- **Max Duration:** 10 minutes
- **Min Duration:** 0.5 seconds
- **Sample Rate:** Any (resampled to 16 kHz)
- **Channels:** Mono or stereo (converted to mono)

## Output

Structured JSON containing:
- Transcript
- Language identification
- AI voice probability
- Detected scam keywords
- Authority impersonation analysis
- Money request detection
- Risk score and level

## Thresholds

### AI Voice Detection
- **Likely AI:** probability >= 0.70
- **Likely Human:** probability <= 0.30
- **Uncertain:** 0.30 < probability < 0.70

### Risk Levels
- **LOW:** 0.00 - 0.29
- **MEDIUM:** 0.30 - 0.59
- **HIGH:** 0.60 - 0.79
- **CRITICAL:** 0.80 - 1.00

## Known Limitations

1. **Language Coverage**
   - Optimized for Hindi and English
   - Hinglish code-switching support is heuristic
   - Performance may degrade for other languages

2. **AI Voice Detection**
   - Probabilistic, not forensic proof
   - Model trained on specific datasets
   - May have domain shift on real-world calls

3. **Keyword Detection**
   - MVP keyword set (extensible)
   - Rule-based (not learned)
   - May miss creative variations

4. **Amount Extraction**
   - Limited Hindi number word support
   - Primarily numeric extraction

5. **Context Understanding**
   - Pattern-based detection
   - May flag innocent contextual mentions

## Ethical Considerations

- **Privacy:** No audio/transcripts logged at INFO level
- **False Positives:** Risk scoring designed for high recall
- **Explainability:** All confidence scores are documented
- **Bias:** Performance may vary by accent, dialect
- **Intended Use:** Scam detection, not surveillance

## Model Versions

| Component | Version | Date |
|-----------|---------|------|
| speech-intelligence | v1.0.0 | 2026-07-11 |
| whisper | base | - |
| voice-spoof | wav2vec2-large-xlsr | - |
| keyword-rules | v1.0 | 2026-07-11 |
| risk-engine | v1.0 | 2026-07-11 |

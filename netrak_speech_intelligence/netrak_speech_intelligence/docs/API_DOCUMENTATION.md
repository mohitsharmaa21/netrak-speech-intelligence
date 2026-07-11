# Netrak Speech Intelligence - API Documentation

## Base URL

```
http://localhost:8000  # Local development
```

## Endpoints

### 1. Health Check

**GET** `/health`

Check service health status.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "netrak-speech-intelligence",
  "version": "1.0.0"
}
```

### 2. Analyze Speech

**POST** `/speech/analyze`

Analyze audio file for scam detection.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body:** Form field `file` containing audio file

**Supported Formats:** `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`

**cURL Example:**
```bash
curl -X POST http://localhost:8000/speech/analyze \
  -F "file=@/path/to/audio.wav" \
  -H "Content-Type: multipart/form-data"
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/speech/analyze"
files = {"file": open("/path/to/audio.wav", "rb")}
response = requests.post(url, files=files)
result = response.json()
print(result)
```

**Response (200 OK):**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "model_version": "speech-intelligence-v1.0.0",
  "transcript": "Main CBI officer bol raha hoon...",
  "detected_language": {
    "code": "hi",
    "name": "Hindi",
    "confidence": 0.94
  },
  "ai_voice": {
    "probability": 0.81,
    "prediction": "likely_ai",
    "confidence": 0.81
  },
  "scam_keywords": [
    {"keyword": "cbi", "category": "authority"},
    {"keyword": "arrest", "category": "threat"}
  ],
  "authority_impersonation": {
    "detected": true,
    "authorities": ["CBI"],
    "confidence": 0.90
  },
  "money_request": {
    "detected": true,
    "payment_methods": ["bank_transfer"],
    "amounts": ["50000"],
    "confidence": 0.93
  },
  "risk": {
    "score": 0.95,
    "level": "CRITICAL",
    "reasons": [
      "Authority impersonation detected: CBI",
      "Money transfer request detected (amounts: 50000)",
      "Threat or arrest language detected"
    ]
  },
  "processing_time_ms": 3450
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "error": "AudioValidationError",
  "message": "Audio too short: 0.3s. Minimum: 0.5s"
}
```

**413 Payload Too Large:**
```json
{
  "error": "AudioTooLargeError",
  "message": "Audio file too large: 30MB. Maximum allowed: 25MB"
}
```

**415 Unsupported Media Type:**
```json
{
  "error": "UnsupportedFormatError",
  "message": "Unsupported format: avi. Supported: wav, mp3, m4a, flac, ogg"
}
```

**500 Internal Server Error:**
```json
{
  "error": "InternalError",
  "message": "Internal server error occurred during analysis"
}
```

## Response Schema

### LanguageResult
```json
{
  "code": "string",  // Language code (e.g., "hi", "en")
  "name": "string",  // Language name (e.g., "Hindi")
  "confidence": 0.0-1.0,  // Confidence score
  "code_switch_detected": true|false|null  // Optional
}
```

### AIVoiceResult
```json
{
  "probability": 0.0-1.0|null,  // AI voice probability
  "prediction": "likely_ai|likely_human|uncertain|unavailable",
  "confidence": 0.0-1.0|null  // Same as probability
}
```

### ScamKeyword
```json
{
  "keyword": "string",
  "category": "string"  // authority, threat, urgency, etc.
}
```

### AuthorityResult
```json
{
  "detected": true|false,
  "authorities": ["string"],  // List of detected authorities
  "confidence": 0.0-1.0
}
```

### MoneyRequestResult
```json
{
  "detected": true|false,
  "payment_methods": ["string"],  // e.g., ["upi", "bank_transfer"]
  "amounts": ["string"],  // e.g., ["50000"]
  "confidence": 0.0-1.0
}
```

### RiskResult
```json
{
  "score": 0.0-1.0,
  "level": "LOW|MEDIUM|HIGH|CRITICAL",
  "reasons": ["string"]  // Human-readable reasons
}
```

## Rate Limiting

No rate limiting in MVP. Production deployment should implement:
- Per-IP rate limits
- Authentication/API keys
- Request throttling

## Backend Integration Notes

1. **Async Processing**
   - For production, consider queueing long audio files
   - Current implementation is synchronous

2. **Logging**
   - Use `request_id` for tracing
   - Transcripts are NOT logged at INFO level (privacy)

3. **Error Handling**
   - Retry on 500 errors
   - Do not retry 4xx errors

4. **Security**
   - Validate file uploads
   - Implement authentication in production
   - Use HTTPS

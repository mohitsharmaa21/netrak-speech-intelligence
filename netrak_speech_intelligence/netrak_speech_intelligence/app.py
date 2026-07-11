"""Netrak Speech Intelligence Service - FastAPI Application"""
import logging
import tempfile
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .services import SpeechIntelligencePipeline
from .services.audio_preprocessor import (
    AudioValidationError,
    UnsupportedFormatError,
    AudioTooLargeError,
    AudioTooShortError,
    AudioTooLongError,
    AudioSilentError
)
from .schemas import SpeechAnalysisResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global pipeline instance
pipeline: SpeechIntelligencePipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global pipeline
    
    # Startup
    logger.info("Starting Netrak Speech Intelligence Service")
    settings = get_settings()
    
    try:
        pipeline = SpeechIntelligencePipeline(settings)
        logger.info("Pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Netrak Speech Intelligence Service")


# Create FastAPI app
app = FastAPI(
    title="Netrak Speech Intelligence Service",
    description="AI-powered speech analysis for scam detection and fraud prevention",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "netrak-speech-intelligence",
        "version": "1.0.0"
    }


@app.post(
    "/speech/analyze",
    response_model=SpeechAnalysisResponse,
    responses={
        200: {"description": "Successful analysis"},
        400: {"model": ErrorResponse, "description": "Invalid or corrupted audio"},
        413: {"model": ErrorResponse, "description": "File too large"},
        415: {"model": ErrorResponse, "description": "Unsupported audio format"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["analysis"]
)
async def analyze_speech(file: UploadFile = File(...)):
    """
    Analyze audio for scam detection
    
    Args:
        file: Audio file (wav, mp3, m4a, flac, ogg)
    
    Returns:
        Complete speech analysis result
    """
    temp_path = None
    
    try:
        logger.info(f"Received analysis request: {file.filename}")
        
        # Validate filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        # Save uploaded file to temporary location
        try:
            # Create temp file
            suffix = os.path.splitext(file.filename)[1]
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_path = temp_file.name
            
            # Write uploaded content
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            
            logger.info(f"Saved upload to: {temp_path}")
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save uploaded file: {str(e)}"
            )
        
        # Run analysis
        try:
            result = pipeline.analyze(temp_path)
            return result
            
        except UnsupportedFormatError as e:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=str(e)
            )
        except AudioTooLargeError as e:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=str(e)
            )
        except (AudioTooShortError, AudioTooLongError, AudioSilentError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except AudioValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during analysis"
        )
    
    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temp file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
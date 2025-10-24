"""
FastAPI Application for UGC Video Metadata Generation

This is a simple prototype that:
1. Provides a 5-step form for user input
2. Accepts video uploads
3. Generates Reuters-style metadata using Gemini
4. Returns structured JSON results
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import json
import os
from datetime import datetime
from typing import Optional

from modules.auth import initialize_auth, get_auth_instance
from modules.gemini_enhancer import GeminiEnhancer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="UGC Video Metadata Generator",
    description="AI-powered metadata generation for Reuters UGC videos",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Gemini enhancer instance
enhancer: Optional[GeminiEnhancer] = None

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Initialize authentication and Gemini on startup"""
    global enhancer
    
    try:
        logger.info("Starting UGC Metadata Generator...")
        
        # Initialize TR authentication
        workspace_id, model_name = initialize_auth()
        logger.info(f"✓ TR Authentication successful - Workspace: {workspace_id}")
        
        # Create Gemini enhancer
        enhancer = GeminiEnhancer()
        logger.info("✓ Gemini Enhancer initialized")
        
        logger.info("=" * 60)
        logger.info("UGC Metadata Generator is ready!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ Startup failed: {e}")
        raise


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root():
    """Serve the main HTML interface"""
    from fastapi.responses import FileResponse
    return FileResponse("app/static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    auth = get_auth_instance()
    return {
        "status": "healthy",
        "workspace_id": auth.workspace_id,
        "model": auth.model_name,
        "gemini_ready": enhancer is not None
    }


@app.post("/api/analyze-video")
async def analyze_video(
    video: UploadFile = File(...),
    event_context: str = Form(...),
    location: str = Form(...),
    date: str = Form(...),
    source: str = Form(...),
    restrictions: str = Form(default="Access all"),
    user_name: Optional[str] = Form(default=None),
    user_email: Optional[str] = Form(default=None),
    verification_location: Optional[str] = Form(default=None),
    verification_date: Optional[str] = Form(default=None)
):
    """
    Analyze a video and generate Reuters-style metadata
    
    This endpoint:
    1. Receives video file and metadata
    2. Saves video temporarily
    3. Analyzes with Gemini
    4. Returns complete Reuters metadata
    5. Saves output to JSON file
    """
    if enhancer is None:
        raise HTTPException(
            status_code=503,
            detail="Gemini enhancer not initialized"
        )
    
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"{timestamp}_{video.filename}"
        video_path = UPLOAD_DIR / video_filename
        
        # Save uploaded video
        logger.info(f"Saving uploaded video: {video_filename}")
        with open(video_path, "wb") as f:
            content = await video.read()
            f.write(content)
        
        file_size_mb = len(content) / 1024 / 1024
        logger.info(f"Video saved: {file_size_mb:.2f} MB")
        
        # Generate metadata
        logger.info("Generating metadata with Gemini...")
        metadata = enhancer.generate_metadata(
            video_path=str(video_path),
            event_context=event_context,
            location=location,
            date=date,
            source=source,
            restrictions=restrictions
        )
        
        # Add user info if provided
        if user_name or user_email:
            metadata['user_info'] = {
                'name': user_name,
                'email': user_email
            }
        
        # Add verification info if provided
        if verification_location or verification_date:
            if 'verification' not in metadata:
                metadata['verification'] = {}
            if verification_location:
                metadata['verification']['location_method'] = verification_location
            if verification_date:
                metadata['verification']['date_method'] = verification_date
        
        # Add processing info
        metadata['processing'] = {
            'timestamp': datetime.now().isoformat(),
            'video_filename': video_filename,
            'video_size_mb': round(file_size_mb, 2)
        }
        
        # Save output to JSON file
        output_filename = f"{timestamp}_metadata.json"
        output_path = OUTPUT_DIR / output_filename
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✓ Metadata generated and saved to: {output_filename}")
        
        # Return metadata
        return JSONResponse(content=metadata)
        
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up uploaded video (optional - comment out to keep files)
        # if video_path.exists():
        #     video_path.unlink()
        pass


@app.get("/api/outputs")
async def list_outputs():
    """List all generated metadata files"""
    try:
        outputs = []
        for file_path in OUTPUT_DIR.glob("*.json"):
            stat = file_path.stat()
            outputs.append({
                "filename": file_path.name,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "size_bytes": stat.st_size
            })
        
        # Sort by creation time, newest first
        outputs.sort(key=lambda x: x['created'], reverse=True)
        
        return {"outputs": outputs, "count": len(outputs)}
        
    except Exception as e:
        logger.error(f"Error listing outputs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/outputs/{filename}")
async def get_output(filename: str):
    """Get a specific metadata output file"""
    try:
        file_path = OUTPUT_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        with open(file_path, 'r') as f:
            metadata = json.load(f)
        
        return JSONResponse(content=metadata)
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error reading output: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

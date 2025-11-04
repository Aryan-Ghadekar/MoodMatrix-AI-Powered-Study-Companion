from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import os
from ppt import process_ppt_file, get_slide_content, extract_text_from_ppt
from quiz import quiz_generator, QuizGenerator
from show import ensure_slide_images,  create_placeholder_base64
from explaination import explanation_generator, ExplanationGenerator
from typing import List, Optional
import uuid
from pathlib import Path
import logging
from dyanamic_timetable import router
import base64
from io import BytesIO
from gtts import gTTS


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SlideSense API")
app.include_router(router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Create necessary directories
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/presentations", exist_ok=True)
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
presentations = {}

@app.get("/")
async def root():
    return {
        "message": "SlideSense API is running",
        "quiz_available": quiz_generator is not None
    }

@app.post("/upload-ppt")
async def upload_ppt(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pptx', '.ppt')):
            raise HTTPException(status_code=400, detail="Only PPT/PPTX files are allowed")
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = f"static/uploads/{unique_filename}"
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Processing PPT file: {file.filename}")
        
        # Process PPT file
        presentation_data = process_ppt_file(file_path)
        logger.info(f"Processed presentation with {presentation_data['total_slides']} slides")
        
        # Generate slide images
        logger.info("Generating slide images...")
        presentation_data = ensure_slide_images(presentation_data, file_path)
        
        # Debug: Check if image URLs are set
        logger.info("Checking image URLs in slides:")
        for i, slide in enumerate(presentation_data["slides"]):
            logger.info(f"Slide {i+1}: image_url = {slide.get('image_url', 'NOT SET')}")
        
        # Store presentation data
        presentations[unique_filename] = {
            "file_path": file_path,
            "data": presentation_data,
            "original_filename": file.filename,
            "unique_filename": unique_filename
        }
        
        logger.info(f"Successfully processed presentation with {presentation_data['total_slides']} slides")
        
        return JSONResponse({
            "success": True,
            "filename": unique_filename,
            "original_filename": file.filename,
            "slides": presentation_data["slides"],
            "total_slides": presentation_data["total_slides"],
            "file_path": file_path
        })
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/presentation/{filename}")
async def get_presentation_data(filename: str):
    try:
        if filename not in presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        return presentations[filename]["data"]
        
    except Exception as e:
        logger.error(f"Error getting presentation data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/slide/{filename}/{slide_index}")
async def get_slide_data(filename: str, slide_index: int):
    try:
        if filename not in presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        file_path = presentations[filename]["file_path"]
        slide_content = get_slide_content(file_path, slide_index)
        return slide_content
        
    except Exception as e:
        logger.error(f"Error getting slide data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/slide-image/{filename}/{slide_index}")
async def get_slide_image(filename: str, slide_index: int):
    """
    Get slide image as base64 or file response
    """
    try:
        if filename not in presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        presentation_data = presentations[filename]["data"]
        
        if slide_index < 0 or slide_index >= len(presentation_data["slides"]):
            raise HTTPException(status_code=400, detail="Invalid slide index")
        
        slide_data = presentation_data["slides"][slide_index]
        
        # Check if image path exists and return the image
        if "image_path" in slide_data and os.path.exists(slide_data["image_path"]):
            return FileResponse(slide_data["image_path"])
        else:
            # Return placeholder image as base64
            placeholder_base64 = create_placeholder_base64()
            return JSONResponse({"base64_image": placeholder_base64, "status": "placeholder"})
            
    except Exception as e:
        logger.error(f"Error getting slide image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/presentation-file/{filename}")
async def get_presentation_file(filename: str):
    """
    Serve the actual PPT file for download or embedding
    """
    try:
        if filename not in presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        file_path = presentations[filename]["file_path"]
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on server")
        
        return FileResponse(
            path=file_path,
            filename=presentations[filename]["original_filename"],
            media_type='application/vnd.ms-powerpoint'
        )
        
    except Exception as e:
        logger.error(f"Error serving presentation file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-quiz/{filename}")
async def generate_quiz(
    filename: str,
    num_questions: int = Query(5, ge=1, le=20),
    slide_numbers: Optional[List[int]] = Query(None),
    question_types: Optional[List[str]] = Query(["mcq"])
):
    """
    Generate quiz from presentation content using AI
    """
    try:
        if quiz_generator is None:
            raise HTTPException(status_code=503, detail="Quiz service is not available")
        
        if filename not in presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        file_path = presentations[filename]["file_path"]
        presentation_data = presentations[filename]["data"]
        
        # Validate slide numbers if provided
        if slide_numbers:
            max_slides = presentation_data["total_slides"]
            invalid_slides = [s for s in slide_numbers if s < 1 or s > max_slides]
            if invalid_slides:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid slide numbers: {invalid_slides}. Available: 1-{max_slides}"
                )
        
        # Generate quiz based on slide selection
        if slide_numbers:
            # Use specific slides
            quiz_data = quiz_generator.generate_quiz_by_slides(
                file_path, slide_numbers, num_questions, question_types
            )
        else:
            # Use all slides
            ppt_text = extract_text_from_ppt(file_path)
            quiz_data = quiz_generator.generate_quiz_from_content(
                ppt_text, num_questions, question_types
            )
        
        # Add presentation metadata
        quiz_data["presentation_info"] = {
            "filename": filename,
            "original_name": presentations[filename]["original_filename"],
            "slides_used": slide_numbers or list(range(1, presentation_data["total_slides"] + 1)),
            "total_slides": presentation_data["total_slides"]
        }
        
        return quiz_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

# ... (keep the rest of your existing routes the same)

@app.get("/available-presentations")
async def get_available_presentations():
    """Get list of uploaded presentations available for quiz generation"""
    available = []
    for filename, pres in presentations.items():
        available.append({
            "filename": filename,
            "original_name": pres["original_filename"],
            "total_slides": pres["data"]["total_slides"],
            "file_path": pres["file_path"]
        })
    
    return {"presentations": available}

@app.get("/presentation-info/{filename}")
async def get_presentation_info(filename: str):
    """Get detailed information about a specific presentation"""
    try:
        if filename not in presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        pres = presentations[filename]
        return {
            "filename": filename,
            "original_name": pres["original_filename"],
            "total_slides": pres["data"]["total_slides"],
            "file_path": pres["file_path"],
            "slides": pres["data"]["slides"]
        }
        
    except Exception as e:
        logger.error(f"Error getting presentation info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    images_dir_exists = os.path.exists("static/images")
    images_count = 0
    if images_dir_exists:
        for root, dirs, files in os.walk("static/images"):
            images_count += len([f for f in files if f.endswith('.png')])
    
    return {
        "status": "healthy",
        "quiz_service": "available" if quiz_generator else "unavailable",
        "presentations_count": len(presentations),
        "upload_directory": os.path.exists("static/uploads"),
        "images_directory": images_dir_exists,
        "total_slide_images": images_count
    }

@app.post("/generate-tts")
async def generate_tts(text: str):
    """
    Generate Text-to-Speech audio from text
    """
    try:
        # Validate text length
        if len(text) > 4000:
            raise HTTPException(status_code=400, detail="Text too long for TTS. Maximum 4000 characters.")
        
        # Create gTTS object
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save to bytes buffer
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Convert to base64
        audio_base64 = base64.b64encode(audio_buffer.getvalue()).decode('utf-8')
        
        return {
            "success": True,
            "audio_base64": audio_base64,
            "text_length": len(text),
            "message": "TTS generated successfully"
        }
        
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        # Fallback to browser TTS
        return {
            "success": True,
            "text": text,
            "message": "Use browser's speech synthesis",
            "use_browser_tts": True
        }

@app.post("/generate-explanation/{filename}")
async def generate_explanation(
    filename: str,
    explanation_type: str = Query("detailed", regex="^(detailed|simple|key_points)$"),
    slide_numbers: Optional[List[int]] = Query(None),
    slide_by_slide: bool = Query(False)
):
    """
    Generate explanation from presentation content using AI
    """
    try:
        if explanation_generator is None:
            raise HTTPException(status_code=503, detail="Explanation service is not available")
        
        if filename not in presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        file_path = presentations[filename]["file_path"]
        presentation_data = presentations[filename]["data"]
        
        # Validate slide numbers if provided
        if slide_numbers:
            max_slides = presentation_data["total_slides"]
            invalid_slides = [s for s in slide_numbers if s < 1 or s > max_slides]
            if invalid_slides:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid slide numbers: {invalid_slides}. Available: 1-{max_slides}"
                )
        else:
            # Use all slides if none specified
            slide_numbers = list(range(1, presentation_data["total_slides"] + 1))
        
        # Generate explanation based on selection
        if slide_by_slide:
            # Generate individual explanations for each slide
            explanation_data = explanation_generator.generate_slide_by_slide_explanation(
                file_path, slide_numbers
            )
        else:
            # Generate combined explanation
            if slide_numbers:
                explanation_data = explanation_generator.generate_explanation_by_slides(
                    file_path, slide_numbers, explanation_type
                )
            else:
                ppt_text = extract_text_from_ppt(file_path)
                explanation_data = explanation_generator.generate_explanation_from_content(
                    ppt_text, explanation_type
                )
        
        # Add presentation metadata
        explanation_data["presentation_info"] = {
            "filename": filename,
            "original_name": presentations[filename]["original_filename"],
            "slides_used": slide_numbers,
            "total_slides": presentation_data["total_slides"],
            "explanation_type": explanation_type,
            "slide_by_slide": slide_by_slide
        }
        
        return explanation_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Explanation generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Explanation generation failed: {str(e)}")

@app.get("/explanation-types")
async def get_explanation_types():
    """Get available explanation types"""
    return {
        "explanation_types": [
            {
                "value": "detailed",
                "label": "Detailed Explanation",
                "description": "Comprehensive, in-depth explanations covering all concepts"
            },
            {
                "value": "simple", 
                "label": "Simple Explanation",
                "description": "Simplified explanations suitable for beginners"
            },
            {
                "value": "key_points",
                "label": "Key Points",
                "description": "Main key points and takeaways from the content"
            }
        ],
        "slide_by_slide": {
            "label": "Slide-by-Slide Explanation",
            "description": "Generate individual explanations for each selected slide"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
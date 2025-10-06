from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import os
from ppt import process_ppt_file, get_slide_content, extract_text_from_ppt, save_uploaded_ppt
from quiz import quiz_generator, QuizGenerator
from typing import List, Optional
import json
import uuid
from pathlib import Path

app = FastAPI(title="SlideSense API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/presentations", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store presentations in memory (in production, use a database)
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
        
        # Process PPT file
        presentation_data = process_ppt_file(file_path)
        
        # Store presentation data
        presentations[unique_filename] = {
            "file_path": file_path,
            "data": presentation_data,
            "original_filename": file.filename,
            "unique_filename": unique_filename
        }
        
        return JSONResponse({
            "success": True,
            "filename": unique_filename,
            "original_filename": file.filename,
            "slides": presentation_data["slides"],
            "total_slides": presentation_data["total_slides"],
            "file_path": file_path
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/presentation/{filename}")
async def get_presentation_data(filename: str):
    try:
        if filename not in presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        return presentations[filename]["data"]
        
    except Exception as e:
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
    
    Args:
        filename: Name of the uploaded presentation
        num_questions: Number of questions to generate (1-20)
        slide_numbers: Specific slides to use (if None, use all slides)
        question_types: Types of questions (mcq, true_false, short_answer, fill_blank)
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
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

@app.post("/generate-quiz-from-text")
async def generate_quiz_from_text(
    content: str,
    num_questions: int = Query(5, ge=1, le=20),
    question_types: Optional[List[str]] = Query(["mcq"])
):
    """
    Generate quiz directly from text content
    """
    try:
        if quiz_generator is None:
            raise HTTPException(status_code=503, detail="Quiz service is not available")
        
        quiz_data = quiz_generator.generate_quiz_from_content(content, num_questions, question_types)
        return quiz_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "quiz_service": "available" if quiz_generator else "unavailable",
        "presentations_count": len(presentations),
        "upload_directory": os.path.exists("static/uploads")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
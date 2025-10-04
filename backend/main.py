from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
from ppt import process_ppt_file, get_slide_content, extract_text_from_ppt
import json

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
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "SlideSense API is running"}

@app.post("/upload-ppt")
async def upload_ppt(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pptx', '.ppt')):
            raise HTTPException(status_code=400, detail="Only PPT/PPTX files are allowed")
        
        # Save uploaded file
        file_path = f"static/uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process PPT file
        presentation_data = process_ppt_file(file_path)
        
        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "slides": presentation_data["slides"],
            "total_slides": presentation_data["total_slides"],
            "file_path": file_path
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/presentation/{filename}")
async def get_presentation_data(filename: str):
    try:
        file_path = f"static/uploads/{filename}"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        presentation_data = process_ppt_file(file_path)
        return presentation_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/slide/{filename}/{slide_index}")
async def get_slide_data(filename: str, slide_index: int):
    try:
        file_path = f"static/uploads/{filename}"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        slide_content = get_slide_content(file_path, slide_index)
        return slide_content
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-quiz/{filename}")
async def generate_quiz(filename: str):
    try:
        file_path = f"static/uploads/{filename}"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        # Extract text from PPT
        ppt_text = extract_text_from_ppt(file_path)
        
        # For now, return mock quiz data
        # In production, integrate with your LLM API here
        quiz_data = {
            "questions": [
                {
                    "id": 1,
                    "question": "What is the main topic of this presentation?",
                    "options": [
                        "Technology Trends",
                        "Business Strategy", 
                        "Market Analysis",
                        "Product Development"
                    ],
                    "correct_answer": 0
                },
                {
                    "id": 2,
                    "question": "Which quarter showed the highest growth?",
                    "options": [
                        "Q1",
                        "Q2",
                        "Q3", 
                        "Q4"
                    ],
                    "correct_answer": 1
                }
            ]
        }
        
        return quiz_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
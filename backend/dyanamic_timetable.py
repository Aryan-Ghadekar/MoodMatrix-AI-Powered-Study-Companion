from fastapi import HTTPException, APIRouter
from typing import Dict, List, Set
from pydantic import BaseModel
import json
from pathlib import Path
from collections import defaultdict

timetable_router = APIRouter(
    prefix="/timetable",
    tags=["Timetable Routes"]
)

# Pydantic models for request/response
class SubjectConfig(BaseModel):
    name: str
    count: int
    difficulty: str

class TimetableRequest(BaseModel):
    subjects: List[SubjectConfig]

# Subject difficulty classification will be dynamic based on frontend input
def get_subjects_by_difficulty(subjects: Dict[str, int], subject_difficulties: Dict[str, str]) -> tuple:
    """Separate subjects into hard and easy categories based on difficulty level"""
    hard = {}
    easy = {}
    
    for subject, count in subjects.items():
        difficulty = subject_difficulties.get(subject, "medium").lower()
        if difficulty == "hard":
            hard[subject] = count
        elif difficulty == "easy":
            easy[subject] = count
        else:  # medium
            # Treat medium as easy for balanced distribution
            easy[subject] = count
    
    return hard, easy

def calculate_day_average_load(slots: Dict[str, float]) -> float:
    """Calculate average cognitive load for a day"""
    return sum(slots.values()) / len(slots) if slots else 0

def classify_day_load(avg_load: float) -> str:
    """Classify day as high or low cognitive load"""
    return "high" if avg_load >= 0.65 else "low"

def get_available_subject(hard_pool: Dict[str, int], easy_pool: Dict[str, int], 
                          prefer_hard: bool, used_today: Set[str]) -> str:
    """Get an available subject that hasn't been used today"""
    if prefer_hard:
        # Try hard subjects first
        for subject in list(hard_pool.keys()):
            if subject not in used_today:
                hard_pool[subject] -= 1
                if hard_pool[subject] == 0:
                    del hard_pool[subject]
                return subject
        # Fall back to easy subjects
        for subject in list(easy_pool.keys()):
            if subject not in used_today:
                easy_pool[subject] -= 1
                if easy_pool[subject] == 0:
                    del easy_pool[subject]
                return subject
    else:
        # Try easy subjects first
        for subject in list(easy_pool.keys()):
            if subject not in used_today:
                easy_pool[subject] -= 1
                if easy_pool[subject] == 0:
                    del easy_pool[subject]
                return subject
        # Fall back to hard subjects
        for subject in list(hard_pool.keys()):
            if subject not in used_today:
                hard_pool[subject] -= 1
                if hard_pool[subject] == 0:
                    del hard_pool[subject]
                return subject
    return "Self/Revision"

def sort_time_slots(slots: Dict[str, float]) -> List[tuple]:
    """Sort time slots in ascending order"""
    def parse_time(time_slot: str) -> int:
        """Convert time slot to minutes for sorting (e.g., '09:00-10:00' -> 540)"""
        start_time = time_slot.split('-')[0].strip()
        hours, minutes = map(int, start_time.split(':'))
        return hours * 60 + minutes
    
    return sorted(slots.items(), key=lambda x: (parse_time(x[0]), x[1]))

def generate_timetable_logic(cognitive_data: Dict, subjects: Dict[str, int], 
                             subject_difficulties: Dict[str, str]) -> Dict:
    """Core timetable generation logic"""
    # Initialize subject pools
    hard_subjects, easy_subjects = get_subjects_by_difficulty(subjects, subject_difficulties)
    
    # Track subjects used per day
    subjects_used_per_day = defaultdict(set)
    
    # Generate timetable
    timetable = {}
    
    for day, slots in cognitive_data.items():
        timetable[day] = {}
        used_today = set()
        
        # Calculate day's average cognitive load
        avg_load = calculate_day_average_load(slots)
        load_type = classify_day_load(avg_load)
        
        # Sort slots by cognitive load (ascending) and time
        sorted_slots = sort_time_slots(slots)
        
        # Determine subject allocation strategy
        if load_type == "low":
            # Low cognitive load day: More hard subjects, 1-2 easy
            num_slots = len(sorted_slots)
            num_easy_target = min(2, max(1, num_slots // 3))
            easy_assigned = 0
            
            # Assign subjects to slots
            for slot, load in sorted_slots:
                # First try to assign hard subjects
                if hard_subjects and (easy_assigned >= num_easy_target or not easy_subjects):
                    subject = get_available_subject(hard_subjects, {}, prefer_hard=True, used_today=used_today)
                    if subject != "Self/Revision":
                        timetable[day][slot] = subject
                        used_today.add(subject)
                    else:
                        timetable[day][slot] = "Self/Revision"
                # Then assign easy subjects for balance
                elif easy_subjects and easy_assigned < num_easy_target:
                    subject = get_available_subject({}, easy_subjects, prefer_hard=False, used_today=used_today)
                    if subject != "Self/Revision":
                        timetable[day][slot] = subject
                        used_today.add(subject)
                        easy_assigned += 1
                    else:
                        timetable[day][slot] = "Self/Revision"
                else:
                    # Try any remaining subjects
                    subject = get_available_subject(hard_subjects, easy_subjects, prefer_hard=True, used_today=used_today)
                    timetable[day][slot] = subject
                    if subject != "Self/Revision":
                        used_today.add(subject)
        
        else:
            # High cognitive load day: More easy subjects, at least 1 hard
            hard_assigned = False
            
            for slot, load in sorted_slots:
                # Assign at least one hard subject to the lowest load slot
                if not hard_assigned and hard_subjects:
                    subject = get_available_subject(hard_subjects, {}, prefer_hard=True, used_today=used_today)
                    if subject != "Self/Revision":
                        timetable[day][slot] = subject
                        used_today.add(subject)
                        hard_assigned = True
                    else:
                        timetable[day][slot] = "Self/Revision"
                # Prefer easy subjects for remaining slots
                elif easy_subjects or hard_subjects:
                    subject = get_available_subject(hard_subjects, easy_subjects, prefer_hard=False, used_today=used_today)
                    timetable[day][slot] = subject
                    if subject != "Self/Revision":
                        used_today.add(subject)
                else:
                    timetable[day][slot] = "Self/Revision"
        
        subjects_used_per_day[day] = used_today
    
    return {
        "timetable": timetable,
        "summary": {
            "total_slots": sum(len(slots) for slots in cognitive_data.values()),
            "subjects_assigned": subjects,
            "remaining_subjects": {**hard_subjects, **easy_subjects},
            "subjects_per_day": {day: list(subjects) for day, subjects in subjects_used_per_day.items()}
        }
    }

@timetable_router.get("/generate-timetable")
async def generate_timetable_from_file():
    """
    Generate weekly timetable based on cognitive load data from JSON file.
    Reads from cognitive_data.json file.
    Ensures no subject appears twice on the same day.
    """
    try:
        # Read the JSON file
        file_path = Path("cognitive_data.json")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="cognitive_data.json file not found")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        cognitive_data = data.get("cognitive_data", {})
        subjects = data.get("subjects", {})
        
        if not cognitive_data or not subjects:
            raise HTTPException(status_code=400, detail="Invalid data format in JSON file")
        
        # Use default difficulty (hard for Math/Physics/Chemistry, easy for others)
        subject_difficulties = {}
        for subject in subjects.keys():
            if subject in ["Math", "Physics", "Chemistry"]:
                subject_difficulties[subject] = "hard"
            else:
                subject_difficulties[subject] = "easy"
        
        result = generate_timetable_logic(cognitive_data, subjects, subject_difficulties)
        return result
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating timetable: {str(e)}")

@timetable_router.post("/generate-timetable-custom")
async def generate_timetable_custom(request: TimetableRequest):
    """
    Generate weekly timetable with custom subject configuration from frontend.
    Accepts subjects with their counts and difficulty levels.
    """
    try:
        # Read cognitive data from JSON file
        file_path = Path("cognitive_data.json")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="cognitive_data.json file not found")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        cognitive_data = data.get("cognitive_data", {})
        
        if not cognitive_data:
            raise HTTPException(status_code=400, detail="Invalid cognitive data in JSON file")
        
        # Parse subjects from request
        subjects = {}
        subject_difficulties = {}
        
        for subject_config in request.subjects:
            subjects[subject_config.name] = subject_config.count
            subject_difficulties[subject_config.name] = subject_config.difficulty
        
        if not subjects:
            raise HTTPException(status_code=400, detail="No subjects provided")
        
        result = generate_timetable_logic(cognitive_data, subjects, subject_difficulties)
        return result
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating timetable: {str(e)}")

class SaveTimetableRequest(BaseModel):
    name: str
    timetable: Dict
    subjects: List[SubjectConfig]
    created_at: str

@timetable_router.post("/save-timetable")
async def save_timetable(request: SaveTimetableRequest):
    """
    Save a generated timetable to a JSON file.
    """
    try:
        saved_timetables_path = Path("saved_timetables.json")
        
        # Load existing saved timetables or create new
        if saved_timetables_path.exists():
            with open(saved_timetables_path, 'r') as f:
                saved_data = json.load(f)
        else:
            saved_data = {"timetables": []}
        
        # Add new timetable
        timetable_entry = {
            "id": len(saved_data["timetables"]) + 1,
            "name": request.name,
            "timetable": request.timetable,
            "subjects": [s.dict() for s in request.subjects],
            "created_at": request.created_at
        }
        
        saved_data["timetables"].append(timetable_entry)
        
        # Save to file
        with open(saved_timetables_path, 'w') as f:
            json.dump(saved_data, f, indent=2)
        
        return {
            "success": True,
            "message": "Timetable saved successfully",
            "id": timetable_entry["id"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving timetable: {str(e)}")

@timetable_router.get("/saved-timetables")
async def get_saved_timetables():
    """
    Get all saved timetables.
    """
    try:
        saved_timetables_path = Path("saved_timetables.json")
        
        if not saved_timetables_path.exists():
            return {"timetables": []}
        
        with open(saved_timetables_path, 'r') as f:
            saved_data = json.load(f)
        
        return saved_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading saved timetables: {str(e)}")

@timetable_router.delete("/saved-timetables/{timetable_id}")
async def delete_saved_timetable(timetable_id: int):
    """
    Delete a saved timetable by ID.
    """
    try:
        saved_timetables_path = Path("saved_timetables.json")
        
        if not saved_timetables_path.exists():
            raise HTTPException(status_code=404, detail="No saved timetables found")
        
        with open(saved_timetables_path, 'r') as f:
            saved_data = json.load(f)
        
        # Find and remove the timetable
        original_length = len(saved_data["timetables"])
        saved_data["timetables"] = [
            t for t in saved_data["timetables"] if t["id"] != timetable_id
        ]
        
        if len(saved_data["timetables"]) == original_length:
            raise HTTPException(status_code=404, detail="Timetable not found")
        
        # Save updated data
        with open(saved_timetables_path, 'w') as f:
            json.dump(saved_data, f, indent=2)
        
        return {"success": True, "message": "Timetable deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting timetable: {str(e)}")

@timetable_router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Cognitive Load Timetable Generator API",
        "endpoints": {
            "/generate-timetable": "GET - Generate timetable from cognitive_data.json",
            "/generate-timetable-custom": "POST - Generate timetable with custom subject configuration",
            "/save-timetable": "POST - Save a generated timetable",
            "/saved-timetables": "GET - Get all saved timetables",
            "/saved-timetables/{id}": "DELETE - Delete a saved timetable"
        }
    }
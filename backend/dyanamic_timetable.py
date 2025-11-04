from fastapi import APIRouter, Request
from typing import Dict, Any
import numpy as np

router = APIRouter(
    prefix="/timetable",
    tags=["Timetable Routes"]
)

@router.post("/generate_timetable")
async def generate_timetable(request: Request) -> Dict[str, Any]:
    """
    Generates a dynamic timetable based on cognitive load and subject weights.
    Works with dummy or real data.
    """

    body = None
    try:
        body = await request.json()
        cognitive_data = body.get("cognitive_data")
        subjects = body.get("subjects")
    except Exception:
        cognitive_data = None
        subjects = None

    if cognitive_data is None:
        cognitive_data = {
            "09:00-10:00": 0.4,
            "10:00-11:00": 0.9,
            "11:00-12:00": 0.7,
            "14:00-15:00": 0.5,
            "18:00-19:00": 0.65,
        }

    if subjects is None:
        subjects = {
            "Math": 5,
            "Physics": 4,
            "Chemistry": 3,
            "English": 2,
            "History": 1,
        }

    def normalize_dict(d: Dict[str, float]) -> Dict[str, float]:
        values = np.array(list(d.values()), dtype=float)
        if np.ptp(values) == 0: 
            return {k: 0.5 for k in d}
        normalized = (values - np.min(values)) / np.ptp(values)
        return {k: float(v) for k, v in zip(d.keys(), normalized)}

    normalized_focus = normalize_dict(cognitive_data)
    normalized_subjects = normalize_dict(subjects)

    sorted_times = sorted(normalized_focus.items(), key=lambda x: x[1], reverse=True)
    sorted_subjects = sorted(normalized_subjects.items(), key=lambda x: x[1], reverse=True)

    timetable = {}
    for i, (subject, _) in enumerate(sorted_subjects):
        if i < len(sorted_times):
            slot = sorted_times[i][0]
            timetable[slot] = subject
        else:
            break

    return {
        "timetable": timetable,
        "meta": {
            "focus_data_used": cognitive_data,
            "subjects_used": subjects,
            "note": "Dummy data used" if body is None else "Real data supported"
        }
    }
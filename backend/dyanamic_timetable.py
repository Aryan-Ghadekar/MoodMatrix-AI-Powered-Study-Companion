from fastapi import APIRouter, Request
from typing import Dict, Any
from collections import defaultdict
import numpy as np

router = APIRouter(
    prefix="/timetable",
    tags=["Timetable Routes"]
)

@router.post("/generate_timetable")
async def generate_timetable(request: Request) -> Dict[str, Any]:
    """
    Generate a weekly dynamic timetable — assigns multiple subjects per day
    based on focus (cognitive load) and subject difficulty.
    Ensures all days and subjects are covered.
    """
    try:
        body = await request.json()
        cognitive_data = body.get("cognitive_data")
        subjects = body.get("subjects")
    except:
        cognitive_data = None
        subjects = None

    if cognitive_data is None:
        cognitive_data = {
            "Mon": {"09:00-10:00": 0.8, "10:00-11:00": 0.9, "15:00-16:00": 0.7},
            "Tue": {"09:00-10:00": 0.5, "10:00-11:00": 0.6, "15:00-16:00": 0.4},
            "Wed": {"09:00-10:00": 0.7, "10:00-11:00": 0.75, "15:00-16:00": 0.6},
            "Thu": {"09:00-10:00": 0.9, "10:00-11:00": 0.85, "15:00-16:00": 0.8},
            "Fri": {"09:00-10:00": 0.6, "10:00-11:00": 0.7, "15:00-16:00": 0.5},
            "Sat": {"09:00-10:00": 0.4, "10:00-11:00": 0.5, "15:00-16:00": 0.3},
            "Sun": {"09:00-10:00": 0.3, "10:00-11:00": 0.4, "15:00-16:00": 0.2},
        }

    if subjects is None:
        subjects = {
            "Math": 5,
            "Physics": 4,
            "Chemistry": 3,
            "English": 2,
            "History": 1,
        }

    daily_avg = {}
    for day, hours in cognitive_data.items():
        if isinstance(hours, dict):
            avg = sum(hours.values()) / len(hours)
        else:
            avg = hours
        daily_avg[day] = avg

    def normalize_dict(d: Dict[str, float]) -> Dict[str, float]:
        values = np.array(list(d.values()), dtype=float)
        if np.ptp(values) == 0:
            return {k: 0.5 for k in d}
        normalized = (values - np.min(values)) / np.ptp(values)
        return {k: float(v) for k, v in zip(d.keys(), normalized)}

    normalized_days = normalize_dict(daily_avg)
    normalized_subjects = normalize_dict(subjects)

    sorted_days = sorted(normalized_days.items(), key=lambda x: x[1], reverse=True)
    sorted_subjects = sorted(normalized_subjects.items(), key=lambda x: x[1], reverse=True)

    weekly_timetable = defaultdict(list)

    n_days = len(sorted_days)
    n_subjects = len(sorted_subjects)

    hard_subjects = [s for s, w in subjects.items() if w >= 4]
    medium_subjects = [s for s, w in subjects.items() if 2 <= w < 4]
    easy_subjects = [s for s, w in subjects.items() if w < 2]

    for i, (day, focus) in enumerate(sorted_days):
        if focus < 0.7:
            weekly_timetable[day].extend(hard_subjects[:2])  # top 2 hardest
        elif focus < 0.4:
            weekly_timetable[day].extend(medium_subjects[:2])  # next 2 medium
        else:
            weekly_timetable[day].extend(easy_subjects[:2])  # next 2 easy

    all_subjects = set(subjects.keys())
    assigned_subjects = {s for subs in weekly_timetable.values() for s in subs}
    unassigned_subjects = list(all_subjects - assigned_subjects)

    for day, _ in sorted_days:
        if not weekly_timetable[day]: 
            if unassigned_subjects:
                weekly_timetable[day].append(unassigned_subjects.pop(0))
            else:
                weekly_timetable[day].append("Self-study / Revision")

    return {
        "weekly_timetable": dict(weekly_timetable),
        "daily_focus_avg": daily_avg,
        "meta": {
            "note": "Dummy data used" if body is None else "Real data supported",
            "subjects": subjects,
        },
    }
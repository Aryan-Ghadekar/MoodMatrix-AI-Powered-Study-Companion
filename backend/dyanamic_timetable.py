# from fastapi import APIRouter, Request
# from typing import Dict, Any
# from collections import defaultdict
# import numpy as np

# router = APIRouter(
#     prefix="/timetable",
#     tags=["Timetable Routes"]
# )

# @router.post("/generate_timetable")
# async def generate_timetable(request: Request) -> Dict[str, Any]:
#     """
#     Generate a weekly dynamic timetable — assigns multiple subjects per day
#     based on focus (cognitive load) and subject difficulty.
#     Ensures all days and subjects are covered.
#     """
#     try:
#         body = await request.json()
#         cognitive_data = body.get("cognitive_data")
#         subjects = body.get("subjects")
#     except:
#         cognitive_data = None
#         subjects = None

#     if cognitive_data is None:
#         cognitive_data = {
#             "Mon": {"09:00-10:00": 0.8, "10:00-11:00": 0.9, "15:00-16:00": 0.7},
#             "Tue": {"09:00-10:00": 0.5, "10:00-11:00": 0.6, "15:00-16:00": 0.4},
#             "Wed": {"09:00-10:00": 0.7, "10:00-11:00": 0.75, "15:00-16:00": 0.6},
#             "Thu": {"09:00-10:00": 0.9, "10:00-11:00": 0.85, "15:00-16:00": 0.8},
#             "Fri": {"09:00-10:00": 0.6, "10:00-11:00": 0.7, "15:00-16:00": 0.5},
#             "Sat": {"09:00-10:00": 0.4, "10:00-11:00": 0.5, "15:00-16:00": 0.3},
#             "Sun": {"09:00-10:00": 0.3, "10:00-11:00": 0.4, "15:00-16:00": 0.2},
#         }

#     if subjects is None:
#         subjects = {
#             "Math": 5,
#             "Physics": 4,
#             "Chemistry": 3,
#             "English": 2,
#             "History": 1,
#         }

#     daily_avg = {}
#     for day, hours in cognitive_data.items():
#         if isinstance(hours, dict):
#             avg = sum(hours.values()) / len(hours)
#         else:
#             avg = hours
#         daily_avg[day] = avg

#     def normalize_dict(d: Dict[str, float]) -> Dict[str, float]:
#         values = np.array(list(d.values()), dtype=float)
#         if np.ptp(values) == 0:
#             return {k: 0.5 for k in d}
#         normalized = (values - np.min(values)) / np.ptp(values)
#         return {k: float(v) for k, v in zip(d.keys(), normalized)}

#     normalized_days = normalize_dict(daily_avg)
#     normalized_subjects = normalize_dict(subjects)

#     sorted_days = sorted(normalized_days.items(), key=lambda x: x[1], reverse=True)
#     sorted_subjects = sorted(normalized_subjects.items(), key=lambda x: x[1], reverse=True)

#     weekly_timetable = defaultdict(list)

#     n_days = len(sorted_days)
#     n_subjects = len(sorted_subjects)

#     hard_subjects = [s for s, w in subjects.items() if w >= 4]
#     medium_subjects = [s for s, w in subjects.items() if 2 <= w < 4]
#     easy_subjects = [s for s, w in subjects.items() if w < 2]

#     for i, (day, focus) in enumerate(sorted_days):
#         if focus < 0.7:
#             weekly_timetable[day].extend(hard_subjects[:2])  # top 2 hardest
#         elif focus < 0.4:
#             weekly_timetable[day].extend(medium_subjects[:2])  # next 2 medium
#         else:
#             weekly_timetable[day].extend(easy_subjects[:2])  # next 2 easy

#     all_subjects = set(subjects.keys())
#     assigned_subjects = {s for subs in weekly_timetable.values() for s in subs}
#     unassigned_subjects = list(all_subjects - assigned_subjects)

#     for day, _ in sorted_days:
#         if not weekly_timetable[day]: 
#             if unassigned_subjects:
#                 weekly_timetable[day].append(unassigned_subjects.pop(0))
#             else:
#                 weekly_timetable[day].append("Self-study / Revision")

#     return {
#         "weekly_timetable": dict(weekly_timetable),
#         "daily_focus_avg": daily_avg,
#         "meta": {
#             "note": "Dummy data used" if body is None else "Real data supported",
#             "subjects": subjects,
#         },
#     }


# from fastapi import APIRouter, Request
# from typing import Dict, Any
# from collections import defaultdict
# import numpy as np

# router = APIRouter(
#     prefix="/timetable",
#     tags=["Timetable Routes"]
# )

# @router.post("/generate_timetable")
# async def generate_timetable(request: Request) -> Dict[str, Any]:
#     """
#     Generate a weekly dynamic timetable:
#     Assigns subjects to specific time slots based on cognitive load (focus) and subject difficulty.
#     Harder subjects go to higher-focus slots, easier ones to lower-focus slots.
#     """

#     # ----------------------------- #
#     # 1️⃣ Parse request body safely
#     # ----------------------------- #
#     try:
#         body = await request.json()
#         cognitive_data = body.get("cognitive_data")
#         subjects = body.get("subjects")
#     except:
#         cognitive_data = None
#         subjects = None

#     # ----------------------------- #
#     # 2️⃣ Use dummy data if not provided
#     # ----------------------------- #
#     if cognitive_data is None:
#         cognitive_data = {
#             "Mon": {"09:00-10:00": 0.8, "10:00-11:00": 0.9, "15:00-16:00": 0.7},
#             "Tue": {"09:00-10:00": 0.5, "10:00-11:00": 0.6, "15:00-16:00": 0.4},
#             "Wed": {"09:00-10:00": 0.7, "10:00-11:00": 0.75, "15:00-16:00": 0.6},
#             "Thu": {"09:00-10:00": 0.9, "10:00-11:00": 0.85, "15:00-16:00": 0.8},
#             "Fri": {"09:00-10:00": 0.6, "10:00-11:00": 0.7, "15:00-16:00": 0.5},
#             "Sat": {"09:00-10:00": 0.4, "10:00-11:00": 0.5, "15:00-16:00": 0.3},
#             "Sun": {"09:00-10:00": 0.3, "10:00-11:00": 0.4, "15:00-16:00": 0.2},
#         }

#     if subjects is None:
#         subjects = {
#             "Math": 5,
#             "Physics": 4,
#             "Chemistry": 3,
#             "English": 2,
#             "History": 1,
#         }

#     # ----------------------------- #
#     # 3️⃣ Helper: Normalize dict
#     # ----------------------------- #
#     def normalize_dict(d: Dict[str, float]) -> Dict[str, float]:
#         values = np.array(list(d.values()), dtype=float)
#         if np.ptp(values) == 0:
#             return {k: 0.5 for k in d}
#         normalized = (values - np.min(values)) / np.ptp(values)
#         return {k: float(v) for k, v in zip(d.keys(), normalized)}

#     # ----------------------------- #
#     # 4️⃣ Flatten all time slots into list
#     # ----------------------------- #
#     all_slots = []
#     for day, hours in cognitive_data.items():
#         for slot, load in hours.items():
#             all_slots.append((day, slot, load))

#     for day, hours in cognitive_data.items():
#         if isinstance(hours, (int, float)):
#             # If only a single value is given, treat it as the same load for all slots
#             hours = {"Morning": hours, "Afternoon": hours, "Evening": hours}
#         for slot, load in hours.items():
#             flattened_loads.append((day, slot, load))


#     # Sort slots by cognitive load (high → low)
#     sorted_slots = sorted(all_slots, key=lambda x: x[2], reverse=True)

#     # Sort subjects by difficulty (high → low)
#     sorted_subjects = sorted(subjects.items(), key=lambda x: x[1], reverse=True)

#     # ----------------------------- #
#     # 5️⃣ Assign subjects to slots (proportionally by weight)
#     # ----------------------------- #
#     weekly_timetable = defaultdict(dict)

#     # Calculate how many slots each subject should get (based on weight)
#     total_weight = sum(subjects.values())
#     total_slots = len(sorted_slots)
#     slots_per_subject = {
#         subject: max(1, round((weight / total_weight) * total_slots))
#         for subject, weight in subjects.items()
#     }

#     slot_index = 0
#     for subject, _ in sorted_subjects:
#         for _ in range(slots_per_subject[subject]):
#             if slot_index < len(sorted_slots):
#                 day, slot, _ = sorted_slots[slot_index]
#                 weekly_timetable[day][slot] = subject
#                 slot_index += 1

#     # Fill remaining unassigned slots
#     for day, slot, _ in sorted_slots[slot_index:]:
#         if slot not in weekly_timetable[day]:
#             weekly_timetable[day][slot] = "Self-study / Revision"

#     # ----------------------------- #
#     # 6️⃣ Return structured response
#     # ----------------------------- #
#     return {
#         "weekly_timetable": dict(weekly_timetable),
#         "meta": {
#             "note": "Subjects assigned to specific time slots based on cognitive load and difficulty",
#             "subjects": subjects,
#             "total_slots": total_slots,
#         },
#     }


# from fastapi import APIRouter, Request
# from typing import Dict, Any
# from collections import defaultdict
# import numpy as np

# router = APIRouter(
#     prefix="/timetable",
#     tags=["Timetable Routes"]
# )

# @router.post("/generate_timetable")
# async def generate_timetable(request: Request) -> Dict[str, Any]:
#     """
#     Generate a weekly dynamic timetable — assigns subjects to slots
#     based on cognitive load and subject difficulty.
#     Handles both nested and flat input formats safely.
#     """
#     try:
#         body = await request.json()
#         cognitive_data = body.get("cognitive_data")
#         subjects = body.get("subjects")
#     except Exception:
#         cognitive_data = None
#         subjects = None

#     # ✅ Fallback dummy data
#     if cognitive_data is None:
#         cognitive_data = {
#             "Mon": {"09:00-10:00": 0.8, "10:00-11:00": 0.9, "15:00-16:00": 0.7},
#             "Tue": {"09:00-10:00": 0.5, "10:00-11:00": 0.6, "15:00-16:00": 0.4},
#             "Wed": {"09:00-10:00": 0.7, "10:00-11:00": 0.75, "15:00-16:00": 0.6},
#             "Thu": {"09:00-10:00": 0.9, "10:00-11:00": 0.85, "15:00-16:00": 0.8},
#             "Fri": {"09:00-10:00": 0.6, "10:00-11:00": 0.7, "15:00-16:00": 0.5},
#             "Sat": {"09:00-10:00": 0.4, "10:00-11:00": 0.5, "15:00-16:00": 0.3},
#             "Sun": {"09:00-10:00": 0.3, "10:00-11:00": 0.4, "15:00-16:00": 0.2},
#         }

#     if subjects is None:
#         subjects = {
#             "Math": 5,
#             "Physics": 4,
#             "Chemistry": 3,
#             "English": 2,
#             "History": 1,
#         }

#     # ✅ Normalize helper
#     def normalize_dict(d: Dict[str, float]) -> Dict[str, float]:
#         values = np.array(list(d.values()), dtype=float)
#         if np.ptp(values) == 0:
#             return {k: 0.5 for k in d}
#         normalized = (values - np.min(values)) / np.ptp(values)
#         return {k: float(v) for k, v in zip(d.keys(), normalized)}

#     # ✅ Compute daily averages
#     daily_avg = {}
#     for day, hours in cognitive_data.items():
#         if isinstance(hours, dict):
#             avg = sum(hours.values()) / len(hours)
#         else:
#             avg = hours
#         daily_avg[day] = avg

#     normalized_subjects = normalize_dict(subjects)

#     # ✅ Flatten loads safely
#     flattened_loads = []
#     for day, hours in cognitive_data.items():
#         # handle both dict and float input formats
#         if isinstance(hours, (int, float)):
#             hours = {
#                 "09:00-10:00": hours,
#                 "10:00-11:00": hours,
#                 "15:00-16:00": hours
#             }
#         for slot, load in hours.items():
#             flattened_loads.append((day, slot, load))

#     # Sort by cognitive load descending
#     sorted_slots = sorted(flattened_loads, key=lambda x: x[2]) 
#     sorted_subjects = sorted(subjects.items(), key=lambda x: x[1], reverse=True)

#     # Split into hard and easy subjects
#     hard_subjects = [s for s, w in sorted_subjects if w >= np.median(list(subjects.values()))]
#     easy_subjects = [s for s, w in sorted_subjects if w < np.median(list(subjects.values()))]

#     # Alternate pairing
#     paired_subjects = []
#     max_len = max(len(hard_subjects), len(easy_subjects))
#     for i in range(max_len):
#         if i < len(hard_subjects):
#             paired_subjects.append(hard_subjects[i])
#         if i < len(easy_subjects):
#             paired_subjects.append(easy_subjects[i])

#     # Assign subjects to top-performing slots
#     weekly_timetable = defaultdict(dict)
#     # for i, (subject, weight) in enumerate(sorted_subjects):
#     #     if i < len(sorted_slots):
#     #         day, slot, _ = sorted_slots[i]
#     #         weekly_timetable[day][slot] = 
#     for i, subject in enumerate(paired_subjects):
#         if i < len(sorted_slots):
#             day, slot, _ = sorted_slots[i]
#             weekly_timetable[day][slot] = subject


#     # Fill remaining slots with revision/self-study
#     for day, slot, _ in sorted_slots[len(sorted_subjects):]:
#         if slot not in weekly_timetable[day]:
#             weekly_timetable[day][slot] = "Self-study / Revision"

#     return {
#         "weekly_timetable": dict(weekly_timetable),
#         "meta": {
#             "note": "Supports both flat and nested cognitive_data input.",
#             "subjects": subjects
#         }
#     }

# from fastapi import APIRouter, Request
# from typing import Dict, Any
# from collections import defaultdict
# import numpy as np

# router = APIRouter(
#     prefix="/timetable",
#     tags=["Timetable Routes"]
# )

# @router.post("/generate_timetable")
# async def generate_timetable(request: Request) -> Dict[str, Any]:
#     """
#     Generate a weekly dynamic timetable — assigns subjects per day
#     with pairing: one hard + one easy subject (when possible).
#     """
#     try:
#         body = await request.json()
#         cognitive_data = body.get("cognitive_data")
#         subjects = body.get("subjects")
#     except Exception:
#         cognitive_data = None
#         subjects = None

#     # ✅ Fallback dummy data
#     if cognitive_data is None:
#         cognitive_data = {
#             "Mon": {"09:00-10:00": 0.8, "10:00-11:00": 0.9, "15:00-16:00": 0.7},
#             "Tue": {"09:00-10:00": 0.5, "10:00-11:00": 0.6, "15:00-16:00": 0.4},
#             "Wed": {"09:00-10:00": 0.7, "10:00-11:00": 0.75, "15:00-16:00": 0.6},
#             "Thu": {"09:00-10:00": 0.9, "10:00-11:00": 0.85, "15:00-16:00": 0.8},
#             "Fri": {"09:00-10:00": 0.6, "10:00-11:00": 0.7, "15:00-16:00": 0.5},
#             "Sat": {"09:00-10:00": 0.4, "10:00-11:00": 0.5, "15:00-16:00": 0.3},
#             "Sun": {"09:00-10:00": 0.3, "10:00-11:00": 0.4, "15:00-16:00": 0.2},
#         }

#     if subjects is None:
#         subjects = {
#             "Math": 5,
#             "Physics": 3,
#             "Chemistry": 3,
#             "English": 1,
#             "History": 1,
#         }

#     # ✅ Split hard and easy subjects
#     median_difficulty = np.median(list(subjects.values()))
#     hard_subjects = [s for s, w in subjects.items() if w >= median_difficulty]
#     easy_subjects = [s for s, w in subjects.items() if w < median_difficulty]

#     # ✅ Calculate daily average load
#     daily_avg = {
#         day: sum(hours.values()) / len(hours) if isinstance(hours, dict) else hours
#         for day, hours in cognitive_data.items()
#     }

#     # Sort days by focus (low load first = high focus)
#     sorted_days = sorted(daily_avg.items(), key=lambda x: x[1])

#     weekly_timetable = defaultdict(dict)
#     hard_index, easy_index = 0, 0

#     # ✅ Step 1: Pair one hard + one easy subject per high-focus day
#     for day, _ in sorted_days:
#         slots = list(cognitive_data[day].keys())
#         if not slots:
#             continue

#         if hard_index < len(hard_subjects):
#             weekly_timetable[day][slots[0]] = hard_subjects[hard_index]
#             hard_index += 1

#         if easy_index < len(easy_subjects) and len(slots) > 1:
#             weekly_timetable[day][slots[1]] = easy_subjects[easy_index]
#             easy_index += 1

#         # Remaining slots = self-study
#         for slot in slots[2:]:
#             weekly_timetable[day][slot] = "Self-study / Revision"

#     # ✅ Step 2: Fill unassigned days
#         for day, day_data in cognitive_data.items():
#             # Skip invalid or malformed entries
#             if not isinstance(day_data, dict):
#                 print(f"⚠️ Skipping invalid cognitive_data entry for {day}: {day_data}")
#                 continue

#             slots = list(day_data.keys())

#             for slot in slots:
#                 # Your existing timetable logic here
#                 cognitive_load = day_data.get(slot, 0.5)  # fallback if missing
#                 # ... (rest of your timetable creation code)


#         slots = list(day_data.keys())
#         for slot in slots:
#             # your existing timetable generation logic here
#             pass


#     return {
#         "weekly_timetable": dict(weekly_timetable),
#         "meta": {
#             "note": "Each high-focus day gets one hard + one easy subject. Remaining slots are for revision.",
#             "subjects": subjects
#         }
#     }

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
    Generate a weekly dynamic timetable — assigns one hard + one easy subject per day,
    remaining slots are for self-study or revision.
    """
    try:
        body = await request.json()
        cognitive_data = body.get("cognitive_data")
        subjects = body.get("subjects")
    except Exception:
        cognitive_data = None
        subjects = None

    # ✅ Fallback data
    if cognitive_data is None:
        cognitive_data = {
            "Monday": {"09:00-10:00": 0.9, "10:00-11:00": 0.8, "15:00-16:00": 0.6},
            "Tuesday": {"09:00-10:00": 0.7, "10:00-11:00": 0.5, "15:00-16:00": 0.4},
            "Wednesday": {"09:00-10:00": 0.85, "10:00-11:00": 0.75, "15:00-16:00": 0.65},
            "Thursday": {"09:00-10:00": 0.95, "10:00-11:00": 0.9, "15:00-16:00": 0.7},
            "Friday": {"09:00-10:00": 0.6, "10:00-11:00": 0.5, "15:00-16:00": 0.3},
        }

    if subjects is None:
        subjects = {
            "Math": 5,
            "Physics": 4,
            "Chemistry": 3,
            "English": 1,
            "History": 1
        }

    # ✅ Split subjects into hard and easy
    median_difficulty = np.median(list(subjects.values()))
    hard_subjects = [s for s, w in subjects.items() if w >= median_difficulty]
    easy_subjects = [s for s, w in subjects.items() if w < median_difficulty]

    hard_index, easy_index = 0, 0
    weekly_timetable = defaultdict(dict)

    # ✅ Sort days by average focus (higher average = more productive)
    sorted_days = sorted(
        cognitive_data.items(),
        key=lambda x: sum(x[1].values()) / len(x[1]),
        reverse=True
    )

    for day, hours in sorted_days:
        slots = list(hours.keys())
        if not slots:
            continue

        # Assign one hard subject (if any left)
        if hard_index < len(hard_subjects):
            weekly_timetable[day][slots[0]] = hard_subjects[hard_index]
            hard_index += 1

        # Assign one easy subject (if any left)
        if easy_index < len(easy_subjects) and len(slots) > 1:
            weekly_timetable[day][slots[1]] = easy_subjects[easy_index]
            easy_index += 1

        # Fill remaining with Self-study / Revision
        for slot in slots[2:]:
            weekly_timetable[day][slot] = "Self-study / Revision"

    # ✅ If any subjects remain, assign them to days with open slots
    remaining_hard = hard_subjects[hard_index:]
    remaining_easy = easy_subjects[easy_index:]

    for day, hours in weekly_timetable.items():
        for slot in cognitive_data[day]:
            if slot not in hours:
                if remaining_hard:
                    hours[slot] = remaining_hard.pop(0)
                elif remaining_easy:
                    hours[slot] = remaining_easy.pop(0)
                else:
                    hours[slot] = "Self-study / Revision"

    return {
        "weekly_timetable": dict(weekly_timetable),
        "meta": {
            "note": "Each day includes one hard + one easy subject, rest are for revision.",
            "subjects": subjects,
            "color_theme": "Keep color theme as it is."
        }
    }

from typing import List, Literal
from pydantic import BaseModel

# Define nested models for the schema

class WorkoutSet(BaseModel):
    set_number: int  # Set number
    reps: int  # Number of repetitions
    rest_seconds: float  # Rest time in seconds
    set_duration_seconds: float  # Duration of the set in seconds

class Exercise(BaseModel):
    workout_id: str  # Unique ID for the workout
    workout_name: str  # Name of the workout
    workout_type: str  # Type of workout
    workout_img_url: str  # URL for the workout image
    total_time_take: float  # Total time taken for the workout
    workout_equipment: str  # Equipment required for the workout
    workout_category: Literal['Beginner', 'Intermediate', 'Advanced']  # Difficulty level
    workout_sets: List[WorkoutSet]  # List of sets for the workout
    workout_instructions: List[str]  # List of instructions for the workout

# Define the main Pydantic model for the workout plan
class WorkoutPlanModel(BaseModel):
    workout_plan_name: str  # Name of the workout plan
    workout_plan_img_url: str  # URL for the plan's image
    workout_plan_description: str  # Description of the plan
    workout_plan_total_time_seconds: float  # Total time for the plan in seconds
    workout_plan_total_exercises: int  # Total number of exercises in the plan
    exercises: List[Exercise]  # List of exercises in the plan


class WorkoutLanding(BaseModel):
    workoutplans: List[WorkoutPlanModel]
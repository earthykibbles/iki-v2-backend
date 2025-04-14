from typing import List, Optional, Literal
from pydantic import BaseModel

# Define nested models for the schema

class Motivation(BaseModel):
    quote: str  # Motivational quote
    image_url: str  # URL for the motivational image

class Activity(BaseModel):
    activity_title: str  # Title of the activity
    activity_description: str  # Description of the activity
    duration_minutes: int  # Duration of the activity in minutes
    audio_url: Optional[str] # URL for audio (optional)
    video_url: Optional[str] # URL for video (optional)
    image_url: Optional[str]# URL for image (optional)
    tips: List[str]  # List of tips for the activity

class Reflection(BaseModel):
    prompt: str  # Reflection prompt
    journaling_tips: List[str]  # List of journaling tips

class Day(BaseModel):
    day: int  # Day number
    theme: str  # Theme for the day
    difficulty: Literal['Beginner', 'Intermediate', 'Advanced']  # Difficulty level
    motivation: Motivation  # Motivational content for the day
    activities: List[Activity]  # List of activities for the day
    reflection: Reflection  # Reflection content for the day

class Features(BaseModel):
    audio_guide: bool  # Whether audio guide is available
    video_tutorials: bool  # Whether video tutorials are available
    motivational_quotes: bool  # Whether motivational quotes are available
    progress_tracking: bool  # Whether progress tracking is available

# Define the main Pydantic model for the mindfulness plan
class MindfulnessPlanModel(BaseModel):
    mindfulness_plan_name: str  # Name of the mindfulness plan
    mindfulness_plan_img_url: str  # URL for the plan's image
    mindfulness_plan_description: str  # Description of the plan
    mindfulness_plan_total_days: int  # Total number of days in the plan
    features: Features  # Features of the plan
    days: List[Day]  # List of days in the plan

class MindfulnessLanding(BaseModel):
    activities: List[Activity]
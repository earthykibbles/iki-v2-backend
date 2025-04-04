from typing import List
from pydantic import BaseModel

# Define nested models for the schema

class Choice(BaseModel):
    choice_id: int  # Unique ID for the choice
    button_type: int  # Type of button
    button_text: str  # Text displayed on the button
    img_path: str  # Path to the image for the choice

# Define the main Pydantic model for the schema
class QuestionSchema(BaseModel):
    id: int  # Unique ID for the question
    title: str  # Title of the question
    question: str  # The question text
    button_txt: str  # Text for the button
    choices: List[Choice]  # List of choices for the question
    next: bool  # Whether there is a next question
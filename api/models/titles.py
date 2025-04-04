from typing import List
from pydantic import BaseModel

# Define the main Pydantic model for the schema
class TitleSchema(BaseModel):
    title: str  # String
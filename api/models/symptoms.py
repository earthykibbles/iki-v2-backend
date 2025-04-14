from typing import List
from pydantic import BaseModel

# Define the main Pydantic model for the schema
class SymptomsSchema(BaseModel):
    items: List[str]  # Array of strings
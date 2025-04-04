from typing import List
from pydantic import BaseModel

class Suggestion(BaseModel):
    category: str
    suggestions: List[str]

class RecommendationSchema(BaseModel):
    recommendations: List[Suggestion]

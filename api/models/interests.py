from typing import List, Literal
from pydantic import BaseModel

class Tag(BaseModel):
    names: List[str]
    category: Literal['fitness', 'finance', 'mindfulness', 'food', 'mood']

class Interests(BaseModel):
    tags: List[Tag]
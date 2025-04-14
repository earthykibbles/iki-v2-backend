from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Literal

class MealType(str, Enum):
    BREAKFAST = "Breakfast"
    LUNCH = "Lunch"
    DINNER = "Dinner"
    SNACK = "Snacks"

class Meal(BaseModel):
    id: str
    name: str
    thumbnail: str
    description: str
    recipe_id: int
    meal_type: MealType
    serving: int
    serving_description: str
    nutritional_value: str
    ingredients: List[str]
    directions: List[str]
    allergens: List[str]
    rich_in_nutrients : List[str]

class NutritionLanding(BaseModel):
    meals: List[Meal]
from typing import List, Dict
from pydantic import BaseModel, Field

# Model for nutritional data (calories, protein, carbs, fats)
class MacroGoals(BaseModel):
    calories: float
    protein: float
    carbs: float
    fats: float

# Define a nested Pydantic model for a single stage in the nutrition plan
class PlanStage(BaseModel):
    Stage_number: int  # Stage number, must be a positive integer (Pydantic will enforce int type)
    Stage_name: str  # Quirky, motivational name for the stage
    Stage_description: str  # Detailed description of the stage's focus
    Stage_time_period: str  # Duration of the stage (e.g., "4 weeks")
    Expected_outcomes: List[str]  # List of expected outcomes (e.g., ["Lose 3-5 lbs", "Reach 145 lbs"])
    What_to_do: List[str]  # Specific actions to take (e.g., ["Focus on portion control", "Increase vegetable intake"])
    What_to_expect: List[str]  # What the user might experience (e.g., ["Initial weight loss", "Increased energy"])
    Suggested_foods: List[str]  # List of foods to focus on (e.g., ["Leafy greens", "Lean proteins", "Whole grains"])
    Suggested_activity_level: str  # Activity recommendation (e.g., "Moderate: 30 minutes of walking daily")
    Suggested_activities: List[str]  # Specific activities to engage in (e.g., ["Brisk walking", "Yoga"])
    Suggested_avoid_foods: List[str]  # List of foods to avoid (e.g., ["Sugary drinks", "Processed snacks"])
    Suggested_avoid_activities: List[str]  # List of activities to avoid (e.g., ["Prolonged sitting", "Overexertion"])
    Tips_and_tricks: List[str]  # List of helpful tips (e.g., ["Drink water before meals", "Keep healthy snacks on hand"])
    Daily_calorie_goal: float  # Daily calorie target for this stage (e.g., "1800-2000 kcal/day")
    Macronutrient_targets: MacroGoals  # Macronutrient targets (e.g., {"Protein": "30%", "Carbs": "40%", "Fats": "30%"})
    Hydration_goal: str  # Daily hydration goal (e.g., "8 cups of water per day")
    Meal_frequency: str  # Recommended meal frequency (e.g., "3 meals and 2 snacks per day")
    Sleep_recommendation: str  # Sleep recommendation for this stage (e.g., "7-8 hours per night")
    Stress_management_techniques: List[str]  # Techniques to manage stress (e.g., ["Meditation", "Deep breathing"])

# Define the main Pydantic model for the nutrition plan
class NutritionPlan(BaseModel):
    total_time_period_weeks: int  # Total duration of the plan in weeks
    plan_stages: List[PlanStage]  # List of stages in the plan
    user_height: str  # User's height (e.g., "5'10")
    user_current_weight: str  # User's current weight (e.g., "150 lbs")
    user_desired_weight: str  # User's desired weight (e.g., "140 lbs")
    user_bmi: float  # User's BMI
    user_favorite_foods: List[str]  # List of user's favorite foods (e.g., ["Pizza", "Sushi"])
    user_self_assessed_health: str  # User's self-assessed health (e.g., "Healthy")
    user_health_risks: List[str]  # List of identified health risks (e.g., ["Risk of undernutrition"])
    user_dietary_recommendations: List[str]  # General dietary recommendations (e.g., ["Increase vegetable intake"])
    user_predicted_calorie_needs: str  # Predicted daily calorie needs (e.g., "1800-2000 kcal/day")
    plan_goals: List[str]  # Overall goals of the plan (e.g., ["Achieve desired weight of 140 lbs", "Improve energy levels"])
    potential_challenges: List[str]  # Potential challenges (e.g., ["Cravings for unhealthy foods", "Time constraints"])
    motivational_tips: List[str]  # Motivational tips (e.g., ["Celebrate small wins", "Stay consistent"])
    recommended_nutrients: List[str]  # Nutrients to focus on (e.g., ["Protein", "Fiber", "Vitamin D"])
    suggested_supplements: List[str]  # Suggested supplements (e.g., ["Vitamin D", "Omega-3"])
    monitoring_metrics: List[str]  # Metrics to monitor (e.g., ["Weight", "Energy levels", "Sleep quality"])
    success_indicators: List[str]  # Indicators of success (e.g., ["Reaching 140 lbs", "Improved energy"])
    weekly_check_in_goals: List[str]  # Goals for weekly check-ins (e.g., ["Log meals daily", "Complete all workouts"])
    social_support_recommendations: List[str]  # Recommendations for social support (e.g., ["Join a fitness group", "Share goals with a friend"])
    long_term_maintenance_strategies: List[str]  # Strategies for maintaining results (e.g., ["Continue regular exercise", "Monitor portion sizes"])


#######################################################################

class EnhancedProfile(BaseModel):
    health_risks: List[str] #[A brief description of potential health risks]
    dietary_recommendations: List[str] #[Suggestions for a healthy diet]
    predicted_calorie_needs: int #[Estimated daily calorie intake, e.g., '1800-2000 kcal/day']

######################################################################

# Model for nutritional data (calories, protein, carbs, fats)
class Nutrition(BaseModel):
    calories: float
    protein: float
    carbs: float
    fats: float

# Model for food images (food_name and image_url)
class FoodImage(BaseModel):
    food_name: str
    image_url: str  # Previously Optional[str], now a str with default None

# Model for a single meal
class Meal(BaseModel):
    name: str
    ingredients: List[str]
    preparation: str
    nutrition: Nutrition
    images: List[FoodImage]

# Model for the entire meal plan
class MealPlan(BaseModel):
    meals: List[Meal]
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fats: float

########################################################################
# Schemas for everthing inference can do
# Identify food
# Build Recipe
# Get alternatives
# Get calorie content

class FoodIdentity(BaseModel):
    name: str
    description: str
    macro: Nutrition


class Ingredient(BaseModel):
    name: str
    quantity: int
    quantity_unit: str


class FoodIngredients(BaseModel):
    ingredients: List[Ingredient]


class FoodRecipe(BaseModel):
    ingredients: List[Ingredient]
    instructions: List[str]


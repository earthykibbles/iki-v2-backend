# yourapp/utils.py
import openai
from django.conf import settings
from mistralai import Mistral
import json
from django.core.cache import cache
from .schemas import NutritionPlan, EnhancedProfile, MealPlan, FoodIdentity, FoodIngredients, FoodRecipe
import logging
from requests_oauthlib import OAuth1Session
import requests
import os
import asyncio
from PIL import Image
import io
from google import genai

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iki.settings")


OPENAI_API_KEY = settings.OPENAI_API_KEY
MISTRAL_API_KEY = settings.MISTRAL_API_KEY
FATSECRET_API_KEY = settings.FATSECRET_API_KEY  # Add to settings.py
FATSECRET_API_SECRET = settings.FATSECRET_API_SECRET  # Add to settings.py
GOOGLE_API_KEY = settings.GOOGLE_API_KEY


def get_gemini_response(input, image, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([input, image[0], prompt])
    return response.text 

def bytes_to_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    return image

def process_image(image_data, keyword):
    """
    Simulate processing the image with AI and return results as a generator.
    """
    client = genai.Client(api_key=GOOGLE_API_KEY)

    image = bytes_to_image(image_data)
    print(keyword)

    if keyword == "foodid":
        mdu = FoodIdentity
        prompt = "What is this food name?"
    elif keyword == "foodingredients":
        mdu =  FoodIngredients
        prompt = "What ingredients make up this food?"
    elif keyword == "foodrecipe":
        mdu =  FoodRecipe
        prompt = "Give me a proper step b step recipe on cooking this meal."
    else:
        mdu = None
        prompt = ""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[image, prompt],
        config={
            'response_mime_type': 'application/json',
            'response_schema': mdu,
        },
    )
    return response.text


    
def generate_health_insights(profile_data: dict) -> dict:
    """
    Use OpenAI to generate health insights based on the user's profile.
    Args:
        profile_data (dict): The user's profile data.
    Returns:
        dict: Insights including health risks, dietary recommendations, and calorie needs.
    """
    prompt = f"""
    You are a nutrition and health expert. Based on the following user profile, provide:
    1. Potential health risks (e.g., based on BMI, age, self-assessed health).
    2. Dietary recommendations (e.g., based on favorite foods, health status, and goals).
    3. Predicted daily calorie needs (e.g., based on age, height, weight, and goals).

    User Profile:
    - Name: {profile_data['name']}
    - Age: {profile_data['age']}
    - Current Height: {profile_data['current_height']}
    - Current Weight: {profile_data['current_weight']}
    - Desired Weight: {profile_data['desired_weight']}
    - BMI: {profile_data['bmi']}
    - Favorite Foods: {', '.join(profile_data['favorite_foods'])}
    - Self-Assessed Health: {profile_data['self_assessed_health']}
    - Personal Touch Preference: {'Yes' if profile_data['personal_touch_preference'] else 'No'}

    Provide the response in the following format:
    - Health Risks: [A brief description of potential health risks]
    - Dietary Recommendations: [Suggestions for a healthy diet]
    - Predicted Calorie Needs: [Estimated daily calorie intake, e.g., '1800-2000 kcal/day']
    """

    try:
        # client = Mistral(api_key=MISTRAL_API_KEY)


        # completion = client.chat.parse(
        # model="ministral-8b-latest",
        #     messages=[
        #         {
        #             "role": "user",
        #             "content": prompt,
        #         },
        #     ],
        #     response_format=EnhancedProfile,
        # )

        # event = completion.choices[0].message.model_dump_json()
        # print(json.loads(json.loads(event)["content"]))
        # return json.loads(json.loads(event)["content"])

        client = genai.Client(api_key=GOOGLE_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.5-pro-exp-03-25",
            contents=prompt,
            config={
            'response_mime_type': 'application/json',
            'response_schema': EnhancedProfile,
        },
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return {
            "health_risks": "Unable to assess health risks due to an error.",
            "dietary_recommendations": "Unable to provide dietary recommendations due to an error.",
            "predicted_calorie_needs": "Unable to predict calorie needs due to an error."
        }

def generate_nutrition_plan(profile_data: dict, total_time_period_weeks: int = 12) -> dict:
    """
    Use OpenAI to generate a detailed nutrition plan with multiple stages.
    Args:
        profile_data (dict): The user's profile data.
        total_time_period_weeks (int): Total duration of the plan in weeks.
    Returns:
        dict: A nutrition plan with stages.
    """
    num_stages = 3  # Divide the plan into 3 stages (e.g., for a 12-week plan, each stage is 4 weeks)
    stage_duration = total_time_period_weeks // num_stages

    prompt = f"""
    You are a nutrition and health expert. Based on the following user profile, create a detailed strategic nutrition plan
    to help the user achieve their desired weight and improve their health. The plan should be divided into {num_stages} stages,
    with each stage lasting approximately {stage_duration} weeks, for a total of {total_time_period_weeks} weeks.  Give me a common daily macro goal(calories in kcal, 
    proteins, carbs and fat in grams) withing that stage. My measurements are in {profile_data['preferred_unit']} system. 
    Adhere to this to give me accurate advice. Also return my results in the same system. For expected outcomes make sure to mention
    the ranges of weight gain or maintainance or loss I will make. Also give me atleast 5 comprehensive points for each place we need a list

    User Profile:
    - Name: {profile_data['name']}
    - Age: {profile_data['age']}
    - Current Height: {profile_data['current_height']}
    - Current Weight: {profile_data['current_weight']}
    - Desired Weight: {profile_data['desired_weight']}
    - BMI: {profile_data['bmi']}
    - Favorite Foods: {', '.join(profile_data['favorite_foods'])}
    - Self-Assessed Health: {profile_data['self_assessed_health']}
    - Personal Touch Preference: {'Yes' if profile_data['personal_touch_preference'] else 'No'}
    - Health Risks: {profile_data['health_risks']}
    - Dietary Recommendations: {profile_data['dietary_recommendations']}
    - Predicted Calorie Needs: {profile_data['predicted_calorie_needs']}


    Format the response as a list of stages, with eachh stage following the desired structured output.
    """

    try:
        # client = Mistral(api_key=MISTRAL_API_KEY)


        # completion = client.chat.parse(
        # model="ministral-8b-latest",
        #     messages=[
        #         {
        #             "role": "user",
        #             "content": prompt,
        #         },
        #     ],
        #     response_format=NutritionPlan,
        # )

        # event = completion.choices[0].message.model_dump_json()
        # print(json.loads(json.loads(event)["content"]))
        # return json.loads(json.loads(event)["content"])
        client = genai.Client(api_key=GOOGLE_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.5-pro-exp-03-25",
            contents=prompt,
            config={
            'response_mime_type': 'application/json',
            'response_schema': NutritionPlan,
        },
        )
        return json.loads(response.text)

    except Exception as e:
        print(f"OpenAI API error in generating plan: {str(e)}")
        return {
            "total_time_period_weeks": total_time_period_weeks,
            "plan_stages": [
                {
                    "Stage_number": 1,
                    "Stage_name": "Error Stage",
                    "Stage_description": "Unable to generate plan due to an error.",
                    "Stage_time_period": f"{total_time_period_weeks} weeks",
                    "Expected_outcome": "N/A",
                    "What_to_do": "Consult a nutritionist for a personalized plan.",
                    "What_to_expect": "N/A",
                    "Suggested_foods": "N/A",
                    "Suggested_activity_level": "N/A",
                    "Suggested_avoid_foods": "N/A",
                    "Suggested_avoid_activities": "N/A",
                    "Tips_and_tricks": "N/A"
                }
            ]
        }


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def search_fatsecret_foods(query, user_preferences=None, avoid_foods=None):
    """
    Search for foods using the FatSecret API with OAuth 1.0a authentication.
    Args:
        query (str): The food to search for (e.g., "Chicken Breast").
        user_preferences (dict): User dietary preferences/allergens (e.g., {"Vegetarian": True, "Milk": False}).
        avoid_foods (list): List of foods to avoid (e.g., ["Sugary drinks"]).
    Returns:
        list: List of food items with nutritional data, filtered by preferences and avoid_foods.
    """
    # Check cache first
    cache_key = f"fatsecret_foods_{query}"
    cached_foods = cache.get(cache_key)
    if cached_foods is not None:
        logger.info(f"Cache hit for query: {query}")
        return cached_foods

    base_url = "https://platform.fatsecret.com/rest/foods/search/v3"
    params = {
        "method": "food.search.v3",
        "format": "json",
        "search_expression": query,
        "include_food_images": "True",
        "include_food_attributes": "True",
        "max_results": 10,  # Limit results for performance
    }

    # Use OAuth1Session for authentication
    try:
        oauth = OAuth1Session(
            client_key=settings.FATSECRET_API_KEY,
            client_secret=settings.FATSECRET_API_SECRET,
            signature_method="HMAC-SHA1",
            signature_type="query",
        )
        response = oauth.get(base_url, params=params)
        print(response.json())  # For debugging
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        logger.error(f"FatSecret API request failed: {e}")
        raise Exception(f"Failed to load food data: {str(e)}")

    # Parse the response
    data = response.json()
    foods = data.get("foods_search", {}).get("results", {}).get("food", [])
    if not foods:
        logger.warning(f"No foods found for query: {query}")
        return []

    # Filter foods based on user preferences and avoid_foods
    filtered_foods = []
    avoid_foods = [food.lower() for food in (avoid_foods or [])]
    user_preferences = user_preferences or {}

    for food in foods:
        food_name = food["food_name"].lower()
        
        # Skip foods that match avoid_foods
        if any(avoid_food in food_name for avoid_food in avoid_foods):
            continue

        # Check dietary preferences and allergens
        food_attributes = food.get("food_attributes", {})
        preferences = food_attributes.get("preferences", {}).get("preference", [])
        allergens = food_attributes.get("allergens", {}).get("allergen", [])

        skip_food = False
        for pref in preferences:
            pref_name = pref["name"]
            pref_value = pref["value"] == "1"
            if pref_name in user_preferences:
                if user_preferences[pref_name] and not pref_value:
                    skip_food = True
                    break
        if skip_food:
            continue

        for allergen in allergens:
            allergen_name = allergen["name"]
            allergen_value = allergen["value"] == "1"
            if allergen_name in user_preferences and user_preferences.get(allergen_name) == False and allergen_value:
                skip_food = True
                break
        if skip_food:
            continue

        # Extract nutritional data (use the 100g serving for consistency)
        servings = food["servings"]["serving"]
        serving_100g = next((s for s in servings if s["metric_serving_amount"] == "100.000"), servings[0])

        # Safely extract the image URL
        image_url = None
        food_images = food.get("food_images", {})
        if food_images and "food_image" in food_images:
            food_image_list = food_images["food_image"]
            if isinstance(food_image_list, list) and food_image_list:
                # Use the first image if available
                image_url = food_image_list[0].get("image_url")
            else:
                logger.warning(f"No food images available for {food['food_name']}")
        else:
            logger.warning(f"food_images field missing or empty for {food['food_name']}")

        filtered_foods.append({
            "name": food["food_name"],
            "calories": float(serving_100g["calories"]),
            "protein": float(serving_100g["protein"]),
            "carbs": float(serving_100g["carbohydrate"]),
            "fats": float(serving_100g["fat"]),
            "serving_description": serving_100g["serving_description"],
            "image_url": image_url  # Will be None if no image is available
        })

    # Cache the filtered results for 1 hour
    cache.set(cache_key, filtered_foods, timeout=3600)
    logger.info(f"Cached {len(filtered_foods)} foods for query: {query}")
    return filtered_foods

def generate_daily_meal_plan(nutrition_plan, stage_number, date, user_preferences=None):
    """
    Generate a daily meal plan using FatSecret data and AI.
    Args:
        nutrition_plan (NutritionPlan): The user's nutrition plan.
        stage_number (int): The current stage number.
        date (datetime.date): The date for the meal plan.
        user_preferences (dict): User dietary preferences/allergens.
    Returns:
        dict: Meal plan data with meals, total calories, and macronutrients.
    """
    logger.info(f"Generating meal plan for user {nutrition_plan.user.username} on {date}")

    # Find the stage in the nutrition plan
    plan_stages = nutrition_plan.plan_stages
    stage = next((s for s in plan_stages if s["Stage_number"] == stage_number), None)
    if not stage:
        logger.error(f"Stage {stage_number} not found in Nutrition Plan")
        raise ValueError(f"Stage {stage_number} not found in Nutrition Plan")

    suggested_foods = stage["Suggested_foods"]
    avoid_foods = stage["Suggested_avoid_foods"]
    available_foods = []

    # Search for suggested foods using FatSecret
    for food in suggested_foods:
        try:
            foods = search_fatsecret_foods(food, user_preferences, avoid_foods)
            available_foods.extend(foods)
        except Exception as e:
            logger.error(f"Failed to fetch suggested food '{food}' from FatSecret: {e}")
            continue  # Skip this food and continue with others

    # Include user's favorite foods if they align with suggested foods
    favorite_foods = nutrition_plan.user_favorite_foods
    for fav_food in favorite_foods:
        if any(sug_food.lower() in fav_food.lower() for sug_food in suggested_foods) and \
           not any(avoid_food.lower() in fav_food.lower() for avoid_food in avoid_foods):
            try:
                foods = search_fatsecret_foods(fav_food, user_preferences, avoid_foods)
                available_foods.extend(foods)
            except Exception as e:
                logger.error(f"Failed to fetch favorite food '{fav_food}' from FatSecret: {e}")
                continue  # Skip this food and continue with others
    # print(available_foods)

    # Check if any foods were found
    if not available_foods:
        logger.error("No foods available after searching FatSecret.")
        raise ValueError("No foods available to create a meal plan.")

    # Prepare prompt for AI
    prompt = f"""
    You are a nutrition expert. Create a daily meal plan for a user based on the following Nutrition Plan stage:
    - Daily Calorie Goal: {stage['Daily_calorie_goal']}
    - Macronutrient Targets: {', '.join([f'{k}: {v}' for k, v in stage['Macronutrient_targets'].items()])}
    - Suggested Foods: {', '.join(stage['Suggested_foods'])}
    - Suggested Avoid Foods: {', '.join(stage['Suggested_avoid_foods'])}
    - Meal Frequency: {stage['Meal_frequency']}
    - User Favorite Foods: {', '.join(nutrition_plan.user_favorite_foods)}
    - User Dietary Recommendations: {', '.join(nutrition_plan.user_dietary_recommendations)}

    Available foods from FatSecret (nutritional data per 100g):
    {', '.join([f"{food['name']}: {food['calories']} kcal, {food['protein']}g protein, {food['carbs']}g carbs, {food['fats']}g fats" for food in available_foods])}

    Create a daily meal plan for {date.strftime('%Y-%m-%d')} with {stage['Meal_frequency']}. For each meal/snack, provide:
    - Name
    - Ingredients (using the available foods, specify the amount in grams)
    - Preparation instructions
    - Nutritional breakdown (calories, protein, carbs, fats)

    Ensure the total daily calories are within {stage['Daily_calorie_goal']}, and the macronutrient distribution is close to the target. Incorporate the user's favorite foods where possible.
    """

    # Generate meal plan with AI
    try:
        # client = Mistral(api_key=MISTRAL_API_KEY)


        # completion = client.chat.parse(
        # model="ministral-8b-latest",
        #     messages=[
        #         {
        #             "role": "user",
        #             "content": prompt,
        #         },
        #     ],
        #     response_format=MealPlan,
        # )
    

        # event = completion.choices[0].message.model_dump_json()
        # print(json.loads(json.loads(event)["content"]))
        # return json.loads(json.loads(event)["content"])
        client = genai.Client(api_key=GOOGLE_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.5-pro-exp-03-25",
            contents=prompt,
            config={
            'response_mime_type': 'application/json',
            'response_schema': MealPlan,
        },
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"OpenAI API request failed: {e}")
        raise Exception(f"Failed to generate meal plan: {str(e)}")
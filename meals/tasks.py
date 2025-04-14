# meals/tasks.py
from celery import shared_task
import json
from google import genai
from celery import shared_task
from django.conf import settings

from iki.settings import MISTRAL_API_KEY
from meals.models import NutritionPlan, DailyMealPlan
from meals.serializers import DailyMealPlanSerializer
from meals.utils import generate_daily_meal_plan
import redis
import logging
from mistralai import Mistral
import meals.schemas as schemas
logger = logging.getLogger(__name__)
redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)


MISTRAL_API_KEY = settings.MISTRAL_API_KEY

@shared_task(bind=True)
def generate_nutrition_plan_task(self, user_id, profile_data: dict, total_time_period_weeks: int = 12):
    """
    Generate a nutrition plan and save it to the database.
    Args:
        user_id: The ID of the authenticated user.
        profile_data (dict): The user's profile data.
        total_time_period_weeks (int): Total duration of the plan in weeks.
    """
    num_stages = 3
    stage_duration = total_time_period_weeks // num_stages

    prompt = f"""
    You are a nutrition and health expert. Based on the following user profile, create a detailed strategic nutrition plan
    to help the user achieve their desired weight and improve their health. The plan should be divided into {num_stages} stages,
    with each stage lasting approximately {stage_duration} weeks, for a total of {total_time_period_weeks} weeks. Give me a common daily macro goal (calories in kcal, 
    proteins, carbs and fat in grams) within that stage. My measurements are in {profile_data['preferred_unit']} system. 
    Adhere to this to give me accurate advice. Also return my results in the same system. For expected outcomes make sure to mention
    the ranges of weight gain or maintenance or loss I will make. Also give me at least 5 comprehensive points for each place we need a list.

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

    Format the response as a list of stages, with each stage following the desired structured output.
    """

    try:
        client = Mistral(api_key=MISTRAL_API_KEY)


        completion = client.chat.parse(
        model="ministral-8b-latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format = schemas.NutritionPlan,
        )

        event = completion.choices[0].message.model_dump_json()

        print(json.loads(json.loads(event)["content"]))

        plan_data = json.loads(json.loads(event)["content"])

        # return json.loads(json.loads(event)["content"])
        # client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        # response = client.models.generate_content(
        #     model="gemini-2.5-pro-exp-03-25",
        #     contents=prompt,
        #     config={
        #         'response_mime_type': 'application/json',
        #         'response_schema': schemas.NutritionPlan,  # Adjust if schema is elsewhere
        #     },
        # )
        # plan_data = json.loads(response.text)

        # Save to database
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        nutrition_plan = NutritionPlan.objects.create(
            user=user,
            total_time_period_weeks=plan_data['total_time_period_weeks'],
            plan_stages=plan_data['plan_stages'],
            user_height=profile_data['current_height'],
            user_current_weight=profile_data['current_weight'],
            user_desired_weight=profile_data['desired_weight'],
            user_bmi=profile_data['bmi'],
            user_favorite_foods=profile_data['favorite_foods'],
            user_self_assessed_health=profile_data['self_assessed_health'],
            user_health_risks=profile_data['health_risks'],
            user_dietary_recommendations=profile_data['dietary_recommendations'],
            user_predicted_calorie_needs=profile_data['predicted_calorie_needs'],
            plan_goals=plan_data.get('plan_goals', []),
            potential_challenges=plan_data.get('potential_challenges', []),
            motivational_tips=plan_data.get('motivational_tips', []),
            recommended_nutrients=plan_data.get('recommended_nutrients', []),
            suggested_supplements=plan_data.get('suggested_supplements', []),
            monitoring_metrics=plan_data.get('monitoring_metrics', []),
            success_indicators=plan_data.get('success_indicators', []),
            weekly_check_in_goals=plan_data.get('weekly_check_in_goals', []),
            social_support_recommendations=plan_data.get('social_support_recommendations', []),
            long_term_maintenance_strategies=plan_data.get('long_term_maintenance_strategies', [])
        )
        return {'task_id': self.request.id, 'status': 'completed', 'nutrition_plan_id': nutrition_plan.id}

    except Exception as e:
        print(f"Error in generating plan: {str(e)}")
        return {
            'task_id': self.request.id,
            'status': 'failed',
            'error': str(e),
            'total_time_period_weeks': total_time_period_weeks,
            'plan_stages': [{'Stage_number': 1, 'Stage_name': 'Error Stage', 'Stage_description': 'Error occurred'}]
        }


def acquire_lock(lock_key, timeout=300):  # 5-minute timeout
    return redis_client.set(lock_key, "locked", nx=True, ex=timeout)

def release_lock(lock_key):
    redis_client.delete(lock_key)

@shared_task(bind=True)
def generate_daily_meal_plan_task(self, user_id, date_str):
    lock_key = f"meal_plan:user:{user_id}:date:{date_str}"
    if not acquire_lock(lock_key):
        return {
            'status': 'pending',
            'existing_task_id': self.request.id if self.request.id else 'unknown',
            'message': f'Meal plan generation already in progress for {date_str}'
        }

    try:
        # Parse date
        from datetime import datetime
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Fetch user and nutrition plan
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        nutrition_plan = NutritionPlan.objects.filter(user=user).first()
        if not nutrition_plan:
            return {'status': 'failed', 'error': 'No nutrition plan found for user'}

        # Check for existing meal plan
        existing_meal_plan = DailyMealPlan.objects.filter(user=user, date=date).first()
        if existing_meal_plan:
            serializer = DailyMealPlanSerializer(existing_meal_plan)
            return {'status': 'completed', 'result': serializer.data}

        # Generate meal plan
        meal_plan_data = generate_daily_meal_plan(
            nutrition_plan=nutrition_plan,
            stage_number=1,  # Adjust as needed
            date=date,
            user_preferences={"Vegetarian": False, "Milk": False}  # Adjust as needed
        )

        # Add user and related fields
        meal_plan_data["date"] = date.strftime('%Y-%m-%d')
        meal_plan_data["user"] = user.id
        meal_plan_data["nutrition_plan"] = nutrition_plan.id

        # Save to database
        serializer = DailyMealPlanSerializer(data=meal_plan_data)
        if serializer.is_valid():
            serializer.save()
            return {'status': 'completed', 'result': serializer.data}
        else:
            return {'status': 'failed', 'error': serializer.errors}

    except Exception as e:
        logger.error(f"Error in generate_daily_meal_plan_task: {e}")
        return {'status': 'failed', 'error': str(e)}
    finally:
        release_lock(lock_key)
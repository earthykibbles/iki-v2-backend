from django.db import models
from django.conf import settings

class OnboardingQuestion(models.Model):
    # Define question types as choices
    QUESTION_TYPES = (
        ('textbox_input', 'Textbox Input'),
        ('multiple_choice', 'Multiple Choice'),
        ('single_choice', 'Single Choice'),
        ('range_input', 'Range Input'),
    )

    question_number = models.IntegerField(unique=True)
    question_text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    # For multiple_choice and single_choice, store possible options as JSON
    options = models.JSONField(null=True, blank=True)
    # For textbox_input, specify if it's number-specific
    is_number_specific = models.BooleanField(default=False)

    class Meta:
        ordering = ['question_number']
    
    def __str__(self):
        return f"Q{self.question_number}: {self.question_text}"

class UserOnboardingAnswer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(OnboardingQuestion, on_delete=models.CASCADE)
    answer = models.TextField()
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'question')
    
    def __str__(self):
        return f"{self.user}'s answer to Q{self.question.question_number}"


class UserProfile(models.Model):
    UNIT_CHOICES = (
        ('metric', 'Metric'),
        ('imperial', 'Imperial'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    current_height = models.CharField(max_length=20)
    current_weight = models.CharField(max_length=20)
    desired_height = models.CharField(max_length=20)
    desired_weight = models.CharField(max_length=20)
    favorite_foods = models.JSONField()
    self_assessed_health = models.CharField(max_length=20)
    personal_touch_preference = models.BooleanField(default=False)
    bmi = models.FloatField(null=True, blank=True)
    health_risks = models.TextField(null=True, blank=True)
    dietary_recommendations = models.TextField(null=True, blank=True)
    predicted_calorie_needs = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    preferred_unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='imperial')  # New field

    def __str__(self):
        return f"Profile for {self.user.username}"
    
class NutritionPlan(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='nutrition_plan')
    total_time_period_weeks = models.PositiveIntegerField()  # Total duration of the plan in weeks
    plan_stages = models.JSONField()  # List of stages, each following the PlanStage schema
    user_height = models.CharField(max_length=20)  # User's height (e.g., "5'10")
    user_current_weight = models.CharField(max_length=20)  # User's current weight (e.g., "150 lbs")
    user_desired_weight = models.CharField(max_length=20)  # User's desired weight (e.g., "140 lbs")
    user_bmi = models.FloatField()  # User's BMI
    user_favorite_foods = models.JSONField()  # List[str]: User's favorite foods (e.g., ["Pizza", "Sushi"])
    user_self_assessed_health = models.CharField(max_length=20)  # User's self-assessed health (e.g., "Healthy")
    user_health_risks = models.JSONField()  # List[str]: Identified health risks
    user_dietary_recommendations = models.JSONField()  # List[str]: General dietary recommendations
    user_predicted_calorie_needs = models.CharField(max_length=50)  # Predicted daily calorie needs (e.g., "1800-2000 kcal/day")
    plan_goals = models.JSONField()  # List[str]: Overall goals of the plan
    potential_challenges = models.JSONField()  # List[str]: Potential challenges
    motivational_tips = models.JSONField()  # List[str]: Motivational tips
    recommended_nutrients = models.JSONField()  # List[str]: Nutrients to focus on
    suggested_supplements = models.JSONField()  # List[str]: Suggested supplements
    monitoring_metrics = models.JSONField()  # List[str]: Metrics to monitor
    success_indicators = models.JSONField()  # List[str]: Indicators of success
    weekly_check_in_goals = models.JSONField()  # List[str]: Goals for weekly check-ins
    social_support_recommendations = models.JSONField()  # List[str]: Recommendations for social support
    long_term_maintenance_strategies = models.JSONField()  # List[str]: Strategies for maintaining results
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Nutrition Plan for {self.user.username}"


class DailyMealPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_meal_plans')
    nutrition_plan = models.ForeignKey('NutritionPlan', on_delete=models.CASCADE, related_name='daily_meal_plans')
    date = models.DateField()  # The date for this meal plan
    meals = models.JSONField()  # List of meals/snacks (e.g., [{"name": "Spinach Salad", "ingredients": [...], "nutrition": {...}, ...}])
    total_calories = models.FloatField()  # Total calories for the day
    total_protein = models.FloatField()  # Total protein (grams)
    total_carbs = models.FloatField()  # Total carbs (grams)
    total_fats = models.FloatField()  # Total fats (grams)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"Meal Plan for {self.user.username} on {self.date}"
    
class DailyConsumption(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_consumption')
    date = models.DateField()  # The date for this meal plan
    total_calories = models.FloatField()  # Total calories for the day
    total_protein = models.FloatField()  # Total protein (grams)
    total_carbs = models.FloatField()  # Total carbs (grams)
    total_fats = models.FloatField()  # Total fats (grams)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"Daily Consumption for {self.user.username} on {self.date}"


class MealTracking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meal_tracking')
    name = models.CharField(max_length=100)
    date = models.DateField()  # The date for this meal plan
    calories = models.FloatField()  # Total calories for the day
    protein = models.FloatField()  # Total protein (grams)
    carbs = models.FloatField()  # Total carbs (grams)
    fats = models.FloatField()  # Total fats (grams)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # class Meta:
    #     unique_together = ('user', 'name')

    def __str__(self):
        return f"Meal Taken for {self.user.username} on {self.date}"



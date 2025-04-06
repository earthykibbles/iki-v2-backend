from rest_framework import serializers
from .models import OnboardingQuestion, UserOnboardingAnswer, UserProfile, DailyMealPlan, NutritionPlan, DailyConsumption, MealTracking
import json

class OnboardingQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingQuestion
        fields = ['question_number', 'question_text', 'question_type', 'options', 'is_number_specific']

class UserOnboardingAnswerSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(queryset=OnboardingQuestion.objects.all())

    class Meta:
        model = UserOnboardingAnswer
        fields = ['question', 'answer']

    def validate_answer(self, value):
        # Ensure the answer is a string (it should be a JSON string for complex types)
        if not isinstance(value, str):
            raise serializers.ValidationError("Answer must be a string")

        question = self.initial_data.get('question')
        question_obj = OnboardingQuestion.objects.get(id=question)
        question_num = question_obj.question_number

        # Parse the answer if it's a JSON string (for height/weight and favorite foods)
        parsed_value = value
        if question_num in [2, 3, 4]:  # Height/Weight and Favorite Foods
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Answer must be a valid JSON string")

        if question_num in [0, 1]:  # Name and Age
            if question_num == 1:  # Age
                try:
                    age = int(value)
                    if not (1 <= age <= 120):
                        raise ValueError("Age must be between 1 and 120")
                except ValueError:
                    raise serializers.ValidationError("Age must be a valid integer")
        elif question_num in [2, 3]:  # Height and Weight
            if not isinstance(parsed_value, dict):
                raise serializers.ValidationError("Answer must be a dictionary")
            if parsed_value.get('unit') not in ['imperial', 'metric']:
                raise serializers.ValidationError("Unit must be 'imperial' or 'metric'")
            if parsed_value['unit'] == 'imperial':
                height = parsed_value.get('height', '')
                if not isinstance(height, str) or not height.count("'"):
                    raise serializers.ValidationError("Imperial height must be in the format '5'10\"'")
                try:
                    weight = float(parsed_value.get('weight', 0))
                    if not (10 <= weight <= 1000):
                        raise ValueError("Weight must be between 10 and 1000 lbs")
                except (ValueError, TypeError):
                    raise serializers.ValidationError("Weight must be a valid number")
            else:  # Metric
                try:
                    height = float(parsed_value.get('height', 0))
                    if not (50 <= height <= 300):
                        raise ValueError("Height must be between 50 and 300 cm")
                except (ValueError, TypeError):
                    raise serializers.ValidationError("Height must be a valid number")
                try:
                    weight = float(parsed_value.get('weight', 0))
                    if not (5 <= weight <= 500):
                        raise ValueError("Weight must be between 5 and 500 kg")
                except (ValueError, TypeError):
                    raise serializers.ValidationError("Weight must be a valid number")
        elif question_num == 4:  # Favorite Foods
            if not isinstance(parsed_value, list):
                raise serializers.ValidationError("Answer must be a list of foods")
        elif question_num in [5, 6]:  # Yes/No questions
            if value not in ['Yes', 'No']:
                raise serializers.ValidationError("Answer must be 'Yes' or 'No'")

        return value

    def create(self, validated_data):
        user = self.context['request'].user
        return UserOnboardingAnswer.objects.create(
            user=user,
            question=validated_data['question'],
            answer=validated_data['answer']
        )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'name', 'age', 'current_height', 'current_weight', 'desired_height', 'desired_weight',
            'favorite_foods', 'self_assessed_health', 'personal_touch_preference', 'bmi',
            'health_risks', 'dietary_recommendations', 'predicted_calorie_needs', 'preferred_unit'
        ]

class NutritionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = NutritionPlan
        fields = [
            'total_time_period_weeks', 'plan_stages', 'user_height', 'user_current_weight',
            'user_desired_weight', 'user_bmi', 'user_favorite_foods', 'user_self_assessed_health',
            'user_health_risks', 'user_dietary_recommendations', 'user_predicted_calorie_needs',
            'plan_goals', 'potential_challenges', 'motivational_tips', 'recommended_nutrients',
            'suggested_supplements', 'monitoring_metrics', 'success_indicators',
            'weekly_check_in_goals', 'social_support_recommendations',
            'long_term_maintenance_strategies', 'created_at', 'updated_at'
        ]


class DailyMealPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyMealPlan
        fields = [
            'user', 'nutrition_plan', 'date', 'meals', 'total_calories',
            'total_protein', 'total_carbs', 'total_fats', 'created_at', 'updated_at'
        ]


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.FileField()
    keyword = serializers.CharField(required=False)

class DailyConsumptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyConsumption
        fields = [
            'user',
            'date',
            'total_calories',
            'total_protein',
            'total_carbs',
            'total_fats',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """
        Add custom validation if needed
        """
        if data['total_calories'] < 0 or data['total_protein'] < 0 or \
           data['total_carbs'] < 0 or data['total_fats'] < 0:
            raise serializers.ValidationError(
                "Nutritional values cannot be negative"
            )
        return data


class MealTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealTracking
        fields = [
            'user',
            'name',
            'date',
            'calories',
            'protein',
            'carbs',
            'fats',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """
        Add custom validation for meal tracking
        """
        if data['calories'] < 0 or data['protein'] < 0 or \
           data['carbs'] < 0 or data['fats'] < 0:
            raise serializers.ValidationError(
                "Nutritional values cannot be negative"
            )
        return data
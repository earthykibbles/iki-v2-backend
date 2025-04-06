# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, generics
from meals.models import OnboardingQuestion, UserOnboardingAnswer, UserProfile, NutritionPlan, DailyMealPlan, MealTracking, DailyConsumption
from meals.serializers import OnboardingQuestionSerializer, UserOnboardingAnswerSerializer, UserProfileSerializer, NutritionPlanSerializer, DailyMealPlanSerializer
from django.db import DatabaseError, transaction
import json
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime
from .utils import generate_health_insights, generate_nutrition_plan, generate_daily_meal_plan
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from meals.serializers import ImageUploadSerializer, MealTrackingSerializer, DailyConsumptionSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .utils import process_image
import gzip
from rest_framework_simplejwt.authentication import JWTAuthentication


User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated users to access this view

    def post(self, request):
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')

            # Validate input
            if not username or not email or not password:
                return Response({
                    'error': 'Username, email, and password are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if the username or email already exists
            if User.objects.filter(username=username).exists():
                return Response({
                    'error': 'Username already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(email=email).exists():
                return Response({
                    'error': 'Email already exists'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            # Generate JWT tokens for the new user
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            return Response({
                'message': 'User registered successfully',
                'access_token': access_token,
                'refresh_token': refresh_token
            }, status=status.HTTP_201_CREATED)

        except DatabaseError as e:
            return Response({
                'error': 'Database error occurred',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'error': 'An error occurred during registration',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError as e:
            return Response({
                'error': 'Database error occurred',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def options(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def _calculate_progress(self, user, current_question_num):
        total_questions = OnboardingQuestion.objects.count()
        if total_questions == 0:
            return 0
        completed_questions = UserOnboardingAnswer.objects.filter(
            user=user,
            question__question_number__lt=current_question_num
        ).count()
        return round((completed_questions / total_questions) * 100, 1)

    def _calculate_bmi(self, height_weight_data):
        try:
            unit = height_weight_data.get('unit')
            if not unit:
                print(f"Missing unit in height/weight data: {height_weight_data}")
                return None

            weight_str = height_weight_data.get('weight', '0')
            weight = float(weight_str)

            if unit == 'imperial':
                height_str = height_weight_data.get('height', "0'0")
                if not height_str or "'" not in height_str:
                    print(f"Invalid imperial height format: {height_str}")
                    return None
                # Split the height string on the ' character
                feet_str, inches_str = height_str.split("'")
                feet = int(feet_str.strip())
                inches = int(inches_str.strip('"'))  # Remove trailing " if present
                total_inches = feet * 12 + inches
                height_m = total_inches * 0.0254  # Convert inches to meters
                weight_kg = weight * 0.453592  # Convert lbs to kg
            else:  # Metric
                height_str = height_weight_data.get('height', '0')
                height_cm = float(height_str)
                height_m = height_cm / 100  # Convert cm to meters
                weight_kg = weight  # Already in kg

            # Calculate BMI
            bmi = weight_kg / (height_m ** 2)
            return round(bmi, 1)
        except (ValueError, IndexError) as e:
            print(f"Failed to calculate BMI for data: {height_weight_data} - Error: {str(e)}")
            return None

    def _create_or_update_profile(self, user):
        # Get all answers for the user
        answers = UserOnboardingAnswer.objects.filter(user=user).order_by('question__question_number')
        if answers.count() != OnboardingQuestion.objects.count():
            return  # Only create profile if all questions are answered

        # Parse answers
        answer_dict = {answer.question.question_number: answer.answer for answer in answers}

        # Validate and parse answers
        name = answer_dict.get(0, "")
        try:
            age = int(answer_dict.get(1, 0))
            if not (1 <= age <= 120):
                print(f"Invalid age: {age}")
                return
        except ValueError:
            print(f"Invalid age format: {answer_dict.get(1)}")
            return

        # Parse current height and weight (question 2)
        current_data = json.loads(answer_dict.get(2, '{"unit": "imperial", "height": "0\'0", "weight": "0"}'))
        if not isinstance(current_data, dict):
            print(f"Invalid current height/weight format: {current_data}")
            return
        current_height = current_data.get('height', "0'0" if current_data.get('unit') == 'imperial' else '0')
        current_weight = current_data.get('weight', '0')
        preferred_unit = current_data.get('unit', 'imperial')  # Extract the unit preference

        # Parse desired height and weight (question 3)
        desired_data = json.loads(answer_dict.get(3, '{"unit": "imperial", "height": "0\'0", "weight": "0"}'))
        if not isinstance(desired_data, dict):
            print(f"Invalid desired height/weight format: {desired_data}")
            return
        desired_height = desired_data.get('height', "0'0" if desired_data.get('unit') == 'imperial' else '0')
        desired_weight = desired_data.get('weight', '0')

        # Favorite foods (question 4)
        favorite_foods = json.loads(answer_dict.get(4, '[]'))
        if not isinstance(favorite_foods, list):
            print(f"Invalid favorite foods format: {favorite_foods}")
            return

        # Yes/No questions (questions 5 and 6)
        self_assessed_health = "Healthy" if answer_dict.get(5, "No") == "Yes" else "Not Healthy"
        personal_touch = answer_dict.get(6, "No") == "Yes"

        # Calculate BMI using current height and weight
        bmi = self._calculate_bmi(current_data)
        if bmi is None:
            print(f"Failed to calculate BMI for data: {current_data}")
            return

        # Create the base profile data
        profile_data = {
            "name": name,
            "age": age,
            "current_height": current_height,
            "current_weight": current_weight,
            "desired_height": desired_height,
            "desired_weight": desired_weight,
            "favorite_foods": favorite_foods,
            "self_assessed_health": self_assessed_health,
            "personal_touch_preference": personal_touch,
            "bmi": bmi
        }

        # Generate health insights using OpenAI
        insights = generate_health_insights(profile_data)
        profile_data.update(insights)

        # Save the profile to the database
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'name': profile_data['name'],
                'age': profile_data['age'],
                'current_height': profile_data['current_height'],
                'current_weight': profile_data['current_weight'],
                'desired_height': profile_data['desired_height'],
                'desired_weight': profile_data['desired_weight'],
                'favorite_foods': profile_data['favorite_foods'],
                'self_assessed_health': profile_data['self_assessed_health'],
                'personal_touch_preference': profile_data['personal_touch_preference'],
                'bmi': profile_data['bmi'],
                'health_risks': profile_data['health_risks'],
                'dietary_recommendations': profile_data['dietary_recommendations'],
                'predicted_calorie_needs': profile_data['predicted_calorie_needs'],
                'preferred_unit': preferred_unit  # Save the unit preference
                
            }
        )

    def get(self, request):
        question_num = request.query_params.get('question', 0)
        
        try:
            question_num = int(question_num)
            last_answered = UserOnboardingAnswer.objects.filter(
                user=request.user
            ).order_by('-question__question_number').first()
            
            expected_next = 0
            if last_answered:
                expected_next = last_answered.question.question_number + 1
                
            if question_num != expected_next:
                return Response({
                    'error': f'Expected question {expected_next}, got {question_num}',
                    'next_question': expected_next,
                    'progress': self._calculate_progress(request.user, expected_next)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                question = OnboardingQuestion.objects.get(question_number=question_num)
                serializer = OnboardingQuestionSerializer(question)
                response_data = serializer.data
                response_data['progress'] = self._calculate_progress(request.user, question_num)
                return Response(response_data, status=status.HTTP_200_OK)
                
            except OnboardingQuestion.DoesNotExist:
                last_question = OnboardingQuestion.objects.order_by('-question_number').first()
                if last_question and question_num > last_question.question_number:
                    self._create_or_update_profile(request.user)
                    return Response({
                        'stop': True,
                        'message': 'Onboarding completed',
                        'progress': 100.0
                    }, status=status.HTTP_200_OK)
                return Response({
                    'error': 'Invalid question number',
                    'progress': self._calculate_progress(request.user, question_num)
                }, status=status.HTTP_404_NOT_FOUND)
                
        except ValueError:
            return Response({
                'error': 'Question parameter must be an integer',
                'progress': self._calculate_progress(request.user, 0)
            }, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            return Response({
                'error': 'Database error occurred',
                'details': str(e),
                'progress': self._calculate_progress(request.user, question_num)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        try:
            question_num = request.data.get('question')
            if not isinstance(question_num, int):
                return Response({
                    'error': 'Question number must be an integer',
                    'progress': self._calculate_progress(request.user, 0)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                question = OnboardingQuestion.objects.get(question_number=question_num)
            except OnboardingQuestion.DoesNotExist:
                return Response({
                    'error': 'Question does not exist',
                    'progress': self._calculate_progress(request.user, question_num)
                }, status=status.HTTP_404_NOT_FOUND)
            
            last_answered = UserOnboardingAnswer.objects.filter(
                user=request.user
            ).order_by('-question__question_number').first()
            
            expected_next = 0
            if last_answered:
                expected_next = last_answered.question.question_number + 1
                
            if question_num != expected_next:
                return Response({
                    'error': f'Expected answer for question {expected_next}, got {question_num}',
                    'next_question': expected_next,
                    'progress': self._calculate_progress(request.user, expected_next)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Pass the request to the serializer's context
            serializer = UserOnboardingAnswerSerializer(
                data={
                    'question': question.id,
                    'answer': request.data.get('answer')
                },
                context={'request': request}  # Add the request to the context
            )
            
            if serializer.is_valid():
                serializer.save()
                progress = self._calculate_progress(request.user, question_num + 1)
                self._create_or_update_profile(request.user)
                return Response({
                    'message': 'Answer saved successfully',
                    'next_question': question_num + 1,
                    'progress': progress
                }, status=status.HTTP_201_CREATED)
            return Response(
                dict(serializer.errors, progress=self._calculate_progress(request.user, question_num)),
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except DatabaseError as e:
            return Response({
                'error': 'Database error occurred',
                'details': str(e),
                'progress': self._calculate_progress(request.user, question_num)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def options(self, request, *args, **kwargs):
        """
        Handle Preflight OPTIONS requests without authentication.
        """
        return Response(status=status.HTTP_200_OK)

class NutritionPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Check if the user has a profile
            try:
                user_profile = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                return Response({
                    'error': 'User profile not found. Please complete the onboarding process first.'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check if a plan already exists
            try:
                nutrition_plan = NutritionPlan.objects.get(user=request.user)
                serializer = NutritionPlanSerializer(nutrition_plan)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except NutritionPlan.DoesNotExist:
                # Generate a new plan if it doesn't exist
                total_time_period_weeks = 12  # Default to 12 weeks, can be made configurable
                profile_data = UserProfileSerializer(user_profile).data
                plan_data = generate_nutrition_plan(profile_data, total_time_period_weeks)
                print(plan_data)

                # Save the plan to the database
                nutrition_plan = NutritionPlan.objects.create(
                    user=request.user,
                    total_time_period_weeks=plan_data['total_time_period_weeks'],
                    plan_stages=plan_data['plan_stages'],
                    user_height=plan_data['user_height'],
                    user_current_weight=plan_data['user_current_weight'],
                    user_desired_weight=plan_data['user_desired_weight'],
                    user_bmi=plan_data['user_bmi'],
                    user_favorite_foods=plan_data['user_favorite_foods'],
                    user_self_assessed_health=plan_data['user_self_assessed_health'],
                    user_health_risks=plan_data['user_health_risks'],
                    user_dietary_recommendations=plan_data['user_dietary_recommendations'],
                    user_predicted_calorie_needs=plan_data['user_predicted_calorie_needs'],
                    plan_goals=plan_data['plan_goals'],
                    potential_challenges=plan_data['potential_challenges'],
                    motivational_tips=plan_data['motivational_tips'],
                    recommended_nutrients=plan_data['recommended_nutrients'],
                    suggested_supplements=plan_data['suggested_supplements'],
                    monitoring_metrics=plan_data['monitoring_metrics'],
                    success_indicators=plan_data['success_indicators'],
                    weekly_check_in_goals=plan_data['weekly_check_in_goals'],
                    social_support_recommendations=plan_data['social_support_recommendations'],
                    long_term_maintenance_strategies=plan_data['long_term_maintenance_strategies']
                )
                serializer = NutritionPlanSerializer(nutrition_plan)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except DatabaseError as e:
            return Response({
                'error': 'Database error occurred',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DailyMealPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        date_str = request.query_params.get("date")
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if a meal plan already exists for this user and date
        existing_meal_plan = DailyMealPlan.objects.filter(user=user, date=date).first()
        if existing_meal_plan:
            serializer = DailyMealPlanSerializer(existing_meal_plan)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Get the user's nutrition plan
        nutrition_plan = NutritionPlan.objects.filter(user=user).first()
        if not nutrition_plan:
            return Response({"error": "No nutrition plan found for user."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Generate the meal plan using the utility function
            meal_plan_data = generate_daily_meal_plan(
                nutrition_plan=nutrition_plan,
                stage_number=1,  # Adjust based on your logic
                date=date,
                user_preferences={"Vegetarian": False, "Milk": False}  # Adjust based on user preferences
            )

            # Add the user to the data
            meal_plan_data["date"] = date
            meal_plan_data["user"] = user.id
            meal_plan_data["nutrition_plan"] = nutrition_plan.id

            # Use the serializer to create a new MealPlan instance in the database
            serializer = DailyMealPlanSerializer(data=meal_plan_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserMealPlansView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        meal_plans = DailyMealPlan.objects.filter(user=user).order_by("-date")
        serializer = DailyMealPlanSerializer(meal_plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ProcessImageView(APIView):
    permission_classes = [IsAuthenticated]

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            image_file = serializer.validated_data["image"]
            keyword = serializer.validated_data.get("keyword", "")

            try:
                # Read compressed image bytes
                compressed_bytes = image_file.read()

                # Decompress the image
                image_data = gzip.decompress(compressed_bytes)

                json_response = process_image(image_data, keyword)

                return Response(
                    {
                        "message": "image processed successfully",
                        "data": json.loads(json_response),
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class MealTrackingDetailView(generics.RetrieveAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = MealTrackingSerializer
    lookup_field = 'id'

    def get_queryset(self):
        # request.user is automatically set by JWTAuthentication
        user = self.request.user
        # if not user.is_authenticated:
        #     raise PermissionDenied("Authentication required")
        return MealTracking.objects.filter(user=user)

    def get(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except MealTracking.DoesNotExist:
            return Response(
                {"detail": "Meal tracking not found or you don't have permission"},
                status=status.HTTP_404_NOT_FOUND
            )

# POST (create) and GET (list) MealTracking
class MealTrackingListCreateView(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = MealTrackingSerializer

    def get_queryset(self):
        return MealTracking.objects.filter(user=self.request.user)

    def update_daily_consumption(self, meal_data, subtract=False):
        """
        Update or create DailyConsumption based on MealTracking data
        If subtract=True, remove the values instead of adding
        """
        user = self.request.user
        date = meal_data['date']
        
        with transaction.atomic():
            daily_consumption, created = DailyConsumption.objects.get_or_create(
                user=user,
                date=date,
                defaults={
                    'total_calories': 0,
                    'total_protein': 0,
                    'total_carbs': 0,
                    'total_fats': 0
                }
            )
            
            # Add or subtract based on the subtract parameter
            factor = -1 if subtract else 1
            daily_consumption.total_calories += factor * float(meal_data['calories'])
            daily_consumption.total_protein += factor * float(meal_data['protein'])
            daily_consumption.total_carbs += factor * float(meal_data['carbs'])
            daily_consumption.total_fats += factor * float(meal_data['fats'])
            
            # If all values are 0 or negative after subtraction, delete the DailyConsumption
            if (daily_consumption.total_calories <= 0 and 
                daily_consumption.total_protein <= 0 and 
                daily_consumption.total_carbs <= 0 and 
                daily_consumption.total_fats <= 0):
                daily_consumption.delete()
            else:
                daily_consumption.save()
            
            return daily_consumption

    def perform_create(self, serializer):
        # Save the MealTracking instance and update DailyConsumption
        meal_instance = serializer.save(user=self.request.user)
        
        # Prepare meal data for DailyConsumption update
        meal_data = {
            'date': meal_instance.date,
            'calories': meal_instance.calories,
            'protein': meal_instance.protein,
            'carbs': meal_instance.carbs,
            'fats': meal_instance.fats
        }
        
        # Update DailyConsumption
        self.update_daily_consumption(meal_data)

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            data['user'] = request.user.id
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except Exception as e:
            return Response(
                {"detail": f"Error creating meal tracking: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
# class MealTrackingListCreateView(generics.ListCreateAPIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = MealTrackingSerializer

#     def get_queryset(self):
#         # Explicitly getting user from request
#         user = self.request.user
#         # if not user.is_authenticated:
#         #     raise PermissionDenied("Authentication required")
#         return MealTracking.objects.filter(user=user)

#     def perform_create(self, serializer):
#         # Using request.user for creation
#         serializer.save(user=self.request.user)

#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             data['user'] = request.user.id
#             serializer = self.get_serializer(data=data)
#             serializer.is_valid(raise_exception=True)
#             self.perform_create(serializer)
#             headers = self.get_success_headers(serializer.data)
#             return Response(
#                 serializer.data,
#                 status=status.HTTP_201_CREATED,
#                 headers=headers
#             )
#         except TokenError:
#             return Response(
#                 {"detail": "Invalid token"},
#                 status=status.HTTP_401_UNAUTHORIZED
#             )

#     def get(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data)

class MealTrackingDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, meal_id):
        try:
            with transaction.atomic():
                # Get the meal tracking instance
                meal = MealTracking.objects.get(
                    id=meal_id,
                    user=request.user
                )
                
                # Prepare meal data for subtraction
                meal_data = {
                    'date': meal.date,
                    'calories': meal.calories,
                    'protein': meal.protein,
                    'carbs': meal.carbs,
                    'fats': meal.fats
                }
                
                # Create an instance of MealTrackingListCreateView to use its method
                view_instance = MealTrackingListCreateView()
                view_instance.request = request
                view_instance.update_daily_consumption(meal_data, subtract=True)
                
                # Delete the meal
                meal.delete()
                
                return Response(
                    {"detail": "Meal tracking deleted successfully"},
                    status=status.HTTP_204_NO_CONTENT
                )
        except MealTracking.DoesNotExist:
            return Response(
                {"detail": "Meal tracking not found or you don't have permission"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"Error deleting meal tracking: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        

# GET all MealTracking for the authenticated user
class MealTrackingUserListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Explicitly getting user from JWT
            user = request.user
            if not user.is_authenticated:
                return Response(
                    {"detail": "Authentication required"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            meals = MealTracking.objects.filter(user=user)
            serializer = MealTrackingSerializer(meals, many=True)
            return Response(serializer.data)
        except TokenError:
            return Response(
                {"detail": "Invalid token"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
# GET all DailyConsumption for the authenticated user
class DailyConsumptionListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DailyConsumptionSerializer

    def get_queryset(self):
        # Return only the authenticated user's DailyConsumption records
        return DailyConsumption.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# GET single DailyConsumption by date
class DailyConsumptionDetailView(generics.RetrieveAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DailyConsumptionSerializer
    
    # Use date as the lookup field instead of id
    lookup_field = 'date'
    lookup_url_kwarg = 'date'  # This will match the URL parameter name

    def get_queryset(self):
        # Return only the authenticated user's DailyConsumption records
        return DailyConsumption.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except DailyConsumption.DoesNotExist:
            return Response(
                {"detail": "Daily consumption not found for this date"},
                status=status.HTTP_404_NOT_FOUND
            )
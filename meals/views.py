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
from .utils import generate_health_insights, generate_daily_meal_plan
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from meals.serializers import ImageUploadSerializer, MealTrackingSerializer, DailyConsumptionSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .utils import process_image
import gzip
from rest_framework_simplejwt.authentication import JWTAuthentication
from meals.tasks import generate_nutrition_plan_task
from celery.result import AsyncResult
from meals.tasks import generate_daily_meal_plan_task
from datetime import date, datetime

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
                return None
            weight = float(height_weight_data.get('weight', '0'))
            if unit == 'imperial':
                height_str = height_weight_data.get('height', "0'0")
                feet_str, inches_str = height_str.split("'")
                feet = int(feet_str.strip())
                inches = int(inches_str.strip('"'))
                total_inches = feet * 12 + inches
                height_m = total_inches * 0.0254
                weight_kg = weight * 0.453592
            else:
                height_cm = float(height_weight_data.get('height', '0'))
                height_m = height_cm / 100
                weight_kg = weight
            bmi = weight_kg / (height_m ** 2)
            return round(bmi, 1)
        except (ValueError, IndexError):
            return None

    def _create_or_update_profile(self, user):
        answers = UserOnboardingAnswer.objects.filter(user=user).order_by('question__question_number')
        if answers.count() != OnboardingQuestion.objects.count():
            return False
        answer_dict = {answer.question.question_number: answer.answer for answer in answers}
        name = answer_dict.get(0, "")
        age = int(answer_dict.get(1, 0))
        current_data = json.loads(answer_dict.get(2, '{"unit": "imperial", "height": "0\'0", "weight": "0"}'))
        desired_data = json.loads(answer_dict.get(3, '{"unit": "imperial", "height": "0\'0", "weight": "0"}'))
        favorite_foods = json.loads(answer_dict.get(4, '[]'))
        self_assessed_health = "Healthy" if answer_dict.get(5, "No") == "Yes" else "Not Healthy"
        personal_touch = answer_dict.get(6, "No") == "Yes"
        bmi = self._calculate_bmi(current_data)
        if bmi is None:
            return False
        profile_data = {
            "name": name,
            "age": age,
            "current_height": current_data.get('height'),
            "current_weight": current_data.get('weight'),
            "desired_height": desired_data.get('height'),
            "desired_weight": desired_data.get('weight'),
            "favorite_foods": favorite_foods,
            "self_assessed_health": self_assessed_health,
            "personal_touch_preference": personal_touch,
            "bmi": bmi,
            "preferred_unit": current_data.get('unit', 'imperial')
        }
        insights = generate_health_insights(profile_data)  # Assuming this exists
        profile_data.update(insights)
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
                'preferred_unit': profile_data['preferred_unit']
            }
        )
        return True

    def get(self, request):
        try:
            # Check profile existence
            has_profile = UserProfile.objects.filter(user=request.user).exists()
            total_questions = OnboardingQuestion.objects.count()
            answers = UserOnboardingAnswer.objects.filter(user=request.user).order_by('question__question_number')
            progress = self._calculate_progress(request.user, answers.count() + 1 if answers.exists() else 1)

            if has_profile:
                return Response({
                    'has_profile': True,
                    'progress': progress,
                    'next_question': None,
                    'completed': True
                }, status=status.HTTP_200_OK)

            if answers.count() == total_questions:
                self._create_or_update_profile(request.user)
                return Response({
                    'has_profile': UserProfile.objects.filter(user=request.user).exists(),
                    'progress': 100.0,
                    'next_question': None,
                    'completed': True
                }, status=status.HTTP_200_OK)

            next_question = answers.count() if answers.exists() else 0
            question = OnboardingQuestion.objects.get(question_number=next_question)
            serializer = OnboardingQuestionSerializer(question)
            return Response({
                'has_profile': False,
                'progress': progress,
                'next_question': next_question,
                'completed': False,
                'question': serializer.data
            }, status=status.HTTP_200_OK)

        except OnboardingQuestion.DoesNotExist:
            return Response({
                'error': 'Invalid question number',
                'progress': progress
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e),
                'progress': 0
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        # Same as before, with slight adjustments
        question_num = request.data.get('question')
        try:
            question = OnboardingQuestion.objects.get(question_number=question_num)
            last_answered = UserOnboardingAnswer.objects.filter(user=request.user).order_by('-question__question_number').first()
            expected_next = last_answered.question.question_number + 1 if last_answered else 0
            if question_num != expected_next:
                return Response({
                    'error': f'Expected answer for question {expected_next}, got {question_num}',
                    'next_question': expected_next,
                    'progress': self._calculate_progress(request.user, expected_next)
                }, status=status.HTTP_400_BAD_REQUEST)
            serializer = UserOnboardingAnswerSerializer(
                data={'question': question.id, 'answer': request.data.get('answer')},
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                next_num = question_num + 1
                progress = self._calculate_progress(request.user, next_num)
                if next_num >= OnboardingQuestion.objects.count():
                    self._create_or_update_profile(request.user)
                    return Response({
                        'message': 'Onboarding completed',
                        'next_question': None,
                        'progress': 100.0,
                        'completed': True
                    }, status=status.HTTP_201_CREATED)
                return Response({
                    'message': 'Answer saved',
                    'next_question': next_num,
                    'progress': progress
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                # Generate a new plan asynchronously
                profile_data = UserProfileSerializer(user_profile).data
                task = generate_nutrition_plan_task.delay(request.user.id, profile_data, 12)
                return Response({'task_id': task.id, 'status': 'pending'}, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({
                'error': 'An error occurred',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NutritionPlanStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        task_result = AsyncResult(task_id)
        if task_result.ready():
            if task_result.successful():
                result = task_result.result
                if result['status'] == 'completed':
                    nutrition_plan = NutritionPlan.objects.get(id=result['nutrition_plan_id'])
                    serializer = NutritionPlanSerializer(nutrition_plan)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': 'failed',
                        'error': result['error']
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    'status': 'failed',
                    'error': str(task_result.result)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'status': 'pending', 'task_id': task_id}, status=status.HTTP_200_OK)
class DailyMealPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        date_str = request.query_params.get("date")
        try:
            datetime.strptime(date_str, "%Y-%m-%d")  # Validate date format
        except (ValueError, TypeError):
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Trigger Celery task
        task = generate_daily_meal_plan_task.delay(user.id, date_str)
        return Response({'task_id': task.id, 'status': 'pending'}, status=status.HTTP_202_ACCEPTED)

class DailyMealPlanStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        task_result = generate_daily_meal_plan_task.AsyncResult(task_id)
        if task_result.ready():
            result = task_result.result
            if result['status'] == 'completed':
                return Response(result['result'], status=status.HTTP_200_OK)
            elif result['status'] == 'pending':
                return Response({
                    'task_id': result['existing_task_id'],
                    'status': 'pending',
                    'message': result['message']
                }, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'failed', 'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'task_id': task_id, 'status': 'pending'}, status=status.HTTP_200_OK)

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
        # Filter by authenticated user and optionally by date (default to today)
        queryset = DailyConsumption.objects.filter(user=self.request.user)
        date_param = self.request.query_params.get('date', str(date.today()))
        try:
            # Validate date format
            datetime.strptime(date_param, '%Y-%m-%d')
            queryset = queryset.filter(date=date_param)
        except ValueError:
            # If invalid date, return all records
            pass
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            # If no records exist for the date, return a default response
            default_data = {
                'user': request.user.id,
                'date': str(date.today()),
                'total_calories': 0.0,
                'total_protein': 0.0,
                'total_carbs': 0.0,
                'total_fats': 0.0,
                'created_at': None,
                'updated_at': None
            }
            return Response([default_data], status=status.HTTP_200_OK)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DailyConsumptionDetailView(generics.RetrieveAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DailyConsumptionSerializer
    lookup_field = 'date'
    lookup_url_kwarg = 'date'

    def get_queryset(self):
        # Return only the authenticated user's DailyConsumption records
        return DailyConsumption.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        try:
            # Attempt to get the DailyConsumption record for the date
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except DailyConsumption.DoesNotExist:
            # If no record exists, return a default response with zeros
            default_data = {
                'user': request.user.id,
                'date': kwargs.get('date'),
                'total_calories': 0.0,
                'total_protein': 0.0,
                'total_carbs': 0.0,
                'total_fats': 0.0,
                'created_at': None,
                'updated_at': None
            }
            return Response(default_data, status=status.HTTP_200_OK)
"""
URL configuration for ikimeals project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from meals.views import (
    MealTrackingDetailView,
    MealTrackingListCreateView,
    MealTrackingDeleteView,
    MealTrackingUserListView,
    DailyConsumptionListView,
    DailyConsumptionDetailView
)
from meals.views import OnboardingView, UserProfileView, DailyMealPlanView, UserMealPlansView, NutritionPlanView, \
    RegisterView, ProcessImageView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('onboarding/', OnboardingView.as_view(), name='onboarding'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('plan/', NutritionPlanView.as_view(), name='nutrition_plan'),
    path("meal-plan/", DailyMealPlanView.as_view(), name="daily-meal-plan"),
    path("meal-plans/", UserMealPlansView.as_view(), name="user-meal-plans"),
    path("img-inf/", ProcessImageView.as_view(), name="image-inference-endpoint"),
    path('meal-tracking/<int:id>/', MealTrackingDetailView.as_view(), name='meal-tracking-detail'),
    path('meal-tracking/', MealTrackingListCreateView.as_view(), name='meal-tracking-list-create'),
    path('meal-tracking/all/', MealTrackingUserListView.as_view(), name='meal-tracking-user-list'),
    path('meal-tracking/<int:meal_id>/delete/', MealTrackingDeleteView.as_view(),name='meal-tracking-delete'),
    path('daily-consumption/', DailyConsumptionListView.as_view(), name='daily-consumption-list'),
    path('daily-consumption/<str:date>/', DailyConsumptionDetailView.as_view(), name='daily-consumption-detail'),
]

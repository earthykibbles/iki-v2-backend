from django.urls import path
from api.views import *

urlpatterns = [
    path('generate-content/', GenerateContentView.as_view(), name='generate_content'),
    path('fitness-landing/', GenerateFitnessLandingView.as_view(), name='fitness_landing'),
    path('mindfulness-landing/', GenerateMindfulnessLandingView.as_view(), name='mindfulness_landing'),
    path('nutrition-landing/', GenerateNutritionLandingView.as_view(), name='nutrition_landing'),
    path('check-points-balance/', CheckPointsBalanceView.as_view(), name='check_points_balance'),
    path('check-regular-points-balance/', CheckRegularPointsBalanceView.as_view(), name='check_regular_points_balance'),
    path('recharge-points/', RechargePointsView.as_view(), name='recharge_points'),
    path('reconcile-points-balance/', ReconcilePointsBalanceView.as_view(), name='reconcile_points_balance'),
    path('appointment-booking/', AppointmentBookingView.as_view(), name='appointment_booking'),
]

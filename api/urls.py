from django.urls import path
from api.views import *

urlpatterns = [
    path('generate-content/', GenerateContentView.as_view(), name='generate_content'),
    path('generate-content/status/<str:task_id>/', GenerateContentStatusView.as_view(), name='generate_content_status'),
    path('fitness-landing/', GenerateFitnessLandingView.as_view(), name='fitness_landing'),
    path('fitness-landing/status/<str:task_id>/', GenerateFitnessLandingStatusView.as_view(), name='fitness_landing_status'),
    path('mindfulness-landing/', GenerateMindfulnessLandingView.as_view(), name='mindfulness_landing'),
    path('mindfulness-landing/status/<str:task_id>/', GenerateMindfulnessLandingStatusView.as_view(), name='mindfulness_landing_status'),
    path('nutrition-landing/', GenerateNutritionLandingView.as_view(), name='nutrition_landing'),
    path('nutrition-landing/status/<str:task_id>/', GenerateNutritionLandingStatusView.as_view(), name='nutrition_landing_status'),
    path('check-points-balance/', CheckPointsBalanceView.as_view(), name='check_points_balance'),
    path('check-regular-points-balance/', CheckRegularPointsBalanceView.as_view(), name='check_regular_points_balance'),
    path('recharge-points/', RechargePointsView.as_view(), name='recharge_points'),
    path('reconcile-points-balance/', ReconcilePointsBalanceView.as_view(), name='reconcile_points_balance'),
    path('appointment-booking/', AppointmentBookingView.as_view(), name='appointment_booking'),


    ###########################################################
    path('send-call-notification/', SendCallNotificationView.as_view(), name='send_call_notification'),
    path('send-chat-notification/', SendChatNotificationView.as_view(), name='send_chat_notification'),
    path('send-friend-request-notification/', FriendRequestNotificationView.as_view(), name='send_friend_request_notification'),
    path('accept-friend-request-notification/', AcceptFriendRequestNotificationView.as_view(), name='accept_friend_request_notification'),
    path('comment-event/', CommentEventView.as_view(), name='comment_event'),
    path('appointment-set-event/', AppointmentSetEventView.as_view(), name='appointment_set_event'),
    path('post-status-event/', PostStatusEventView.as_view(), name='post_status_event'),
]

from django.apps import AppConfig
from firebase_admin import initialize_app, credentials

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        return
        # # Initialize Firebase Admin SDK
        # try:
        #     # Check if app is already initialized to avoid duplicate initialization
        #     if not firebase_admin._apps:
        #         cred = credentials.Certificate('..\credentials\iki-flutter-firebase-adminsdk-c43kn-69d8ada3fe.json')
        #         initialize_app(cred)
        # except Exception as e:
        #     # Log the error or handle it as needed
        #     print(f"Error initializing Firebase Admin SDK: {str(e)}")

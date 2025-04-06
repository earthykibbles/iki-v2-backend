from django.conf import settings
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from firebase_admin import firestore, messaging
import json
from datetime import datetime
import pytz
from google import genai
from api.models import *  # Your existing model schemas
import requests
import uuid

from api.models import Medicine

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iki.settings")
# Configure timezone and API key
nairobi_tz = pytz.timezone('Africa/Nairobi')

GOOGLE_API_KEY = settings.GOOGLE_API_KEY
FLUTTERWAVE_API_KEY = settings.FLUTTERWAVE_API_KEY

class GenerateContentView(APIView):
    # authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            prompt = request.data.get("prompt")
            schema = request.data.get('schema')

            schema_map = {
                "condition": ChronicCondition,
                "fitness": WorkoutPlanModel,
                "medicine": Medicine,
                "onboarding": QuestionSchema,
                "mindfulness": MindfulnessPlanModel,
                "symptoms": SymptomsSchema,
                "title": TitleSchema,
                "mood": RecommendationSchema
            }
            
            model = schema_map.get(schema)
            if not model:
                return Response({'status': 'error', 'message': 'Invalid schema'}, status=400)

            client = genai.Client(api_key=GOOGLE_API_KEY)
            response = client.models.generate_content(
                model="gemini-2.5-pro-exp-03-25",
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': model
                },
            )

            return Response(json.loads(response.text))

        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=500)

class GenerateFitnessLandingView(APIView):
    def get(self, request):
        try:
            prompt = "generate 10 workout plans that are versatile and great for different peoples."
            client = genai.Client(api_key=GOOGLE_API_KEY)
            
            response = client.models.generate_content(
                model="gemini-2.5-pro-exp-03-25",
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': WorkoutLanding
                },
            )

            # Save to Firestore
            db = firestore.client()
            today = datetime.now(nairobi_tz).strftime('%Y%m%d')
            db.collection('fitness_landings').document(today).set(
                json.loads(response.text)
            )

            return Response(json.loads(response.text))

        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=500)

class GenerateMindfulnessLandingView(APIView):
    def get(self, request):
        try:
            prompt = "generate 7 mindfulness exercises that are versatile and great for different peoples."
            client = genai.Client(api_key=GOOGLE_API_KEY)
            
            response = client.models.generate_content(
                model="gemini-2.5-pro-exp-03-25",
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': MindfulnessLanding
                },
            )

            # Save to Firestore
            db = firestore.client()
            today = datetime.now(nairobi_tz).strftime('%Y%m%d')
            db.collection('mindfulness_landings').document(today).set(
                json.loads(response.text)
            )

            return Response(json.loads(response.text))

        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=500)

class GenerateNutritionLandingView(APIView):
    def get(self, request):
        try:
            prompt = "generate 10 different meals and exhaustively description of how to prepare them that are versatile and great for different peoples."
            client = genai.Client(api_key=GOOGLE_API_KEY)
            
            response = client.models.generate_content(
                model="gemini-2.5-pro-exp-03-25",
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': NutritionLanding
                },
            )

            # Save to Firestore
            db = firestore.client()
            today = datetime.now(nairobi_tz).strftime('%Y%m%d')
            db.collection('nutrition_landings').document(today).set(
                json.loads(response.text)
            )

            return Response(json.loads(response.text))

        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=500)


class CheckPointsBalanceView(APIView):
    # authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            print(request.data)
            # user_id = request.user.id  # Assuming your User model has an 'id' field matching Firebase UID
            cost_points = request.data.get("costPoints")
            user_id =  request.data.get("userId")

            print(user_id)

            if not user_id:
                return Response({'status': 'error', 'message': 'User ID is required'}, status=400)

            db = firestore.client()
            user_doc = db.collection('users').document(user_id).get()

            if not user_doc.exists:
                return Response({'status': 'error', 'message': 'User not found'}, status=404)

            user_data = user_doc.to_dict()
            points_balance = user_data.get('points', 0)

            if points_balance >= cost_points:
                return Response({'status': 'success', 'enoughPoints': True, 'points': points_balance}, status=200)
            else:
                return Response({'status': 'success', 'enoughPoints': False, 'points': points_balance}, status=200)

        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=500)


class CheckRegularPointsBalanceView(APIView):
    # Uncomment these lines to enable JWT authentication
    # authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # In the Cloud Function, user_id comes from request.auth.uid (Firebase auth)
            # For Django without authentication, we'll get it from request.data
            # If using JWT, you could use request.user.id instead
            user_id = request.data.get("userId")  # Matches Cloud Function's manual UID check

            if not user_id:
                return Response(
                    {'status': 'error', 'message': 'User ID is required', 'code': 400},
                    status=400
                )

            # Initialize Firestore client
            db = firestore.client()

            # Fetch user document from Firestore
            user_doc = db.collection('users').document(user_id).get()
            print(user_doc)

            if not user_doc.exists:
                return Response(
                    {'status': 'error', 'message': 'User not found', 'code': 404},
                    status=404
                )

            # Get user data and points balance
            user_data = user_doc.to_dict()
            points_balance = user_data.get('totalPoints', 0)  # Matches Cloud Function's field name

            # Check points balance against costPoints from request
            cost_points = request.data.get("costPoints")
            if points_balance >= cost_points:
                return Response(
                    {'status': 'success', 'enoughPoints': True, 'points': points_balance, 'code': 200},
                    status=200
                )
            else:
                return Response(
                    {'status': 'success', 'enoughPoints': False, 'points': points_balance, 'code': 200},
                    status=200
                )

        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e), 'code': 500},
                status=500
            )
class RechargePointsView(APIView):
    # authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_id = request.data.get('userId')
            points = request.data.get('points')
            phone = request.data.get('phone')

            if not user_id:
                return Response({'status': 'error', 'message': 'User ID is required'}, status=400)

            db = firestore.client()
            user_doc = db.collection('users').document(user_id).get()

            if not user_doc.exists:
                return Response({'status': 'error', 'message': 'User not found'}, status=404)

            user_data = user_doc.to_dict()
            points_balance = user_data.get('points', 20)
            firstname = user_data.get("firstname", "Zen")
            lastname = user_data.get("lastname", "Seeker")
            email = user_data.get("email", "ikiwellnessdev@gmail.com")
            fcm_token = user_data.get("fcm_token", "recharge_astray")

            # Flutterwave STK Push Request
            url = "https://api.flutterwave.com/v3/charges?type=mpesa"
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {FLUTTERWAVE_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "tx_ref": f'ITR-{uuid.uuid4()}',
                "amount": points,
                "currency": "KES",
                "phone_number": phone,
                "fullname": f'{firstname} {lastname}',
                "email": email,
                "meta": {
                    "customer_id": user_id,
                    "fcm_token": fcm_token,
                    "country": "KE",
                    "payment_type": "mpesa",
                    "redirect_url": "https://ikiwellnessdev.co.ke/callback",
                    "order_id": f'IKI-{uuid.uuid4()}',
                }
            }

            print(json.dumps(payload))

            try:
                response = requests.post(url, headers=headers, json=payload)
                print(response.text)
                return Response(json.loads(response.text), status=response.status_code)
            except Exception as e:
                print(e)
                return Response({"status": "error", "message": str(e)}, status=500)

        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=500)


class ReconcilePointsBalanceView(APIView):
    # authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_id = request.user.id
            transaction_ref = request.data.get("transaction_ref")
            added_points = request.data.get('added_points')

            if not user_id:
                return Response({'status': 'error', 'message': 'User ID is required'}, status=400)

            db = firestore.client()
            user_doc = db.collection('users').document(user_id).get()

            if not user_doc.exists:
                return Response({'status': 'error', 'message': 'User not found'}, status=404)

            user_data = user_doc.to_dict()
            points_balance = user_data.get('points', 0)

            # Verify transaction with Flutterwave
            url = "https://api.flutterwave.com/v3/transactions/verify_by_reference"
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {FLUTTERWAVE_API_KEY}",
                "Content-Type": "application/json",
            }

            try:
                response = requests.get(url, params={"tx_ref": transaction_ref}, headers=headers)
                response_json = json.loads(response.text)
                print(response_json)

                # Note: Original code checks for "pending" status, but typically we want "successful"
                # Adjust this condition based on Flutterwave's actual response
                if response_json["data"]["status"] == "successful":  # Changed from "pending" to "successful"
                    new_points = points_balance + int(added_points)
                    db.collection('users').document(user_id).update({"points": new_points})

                    # Log transaction
                    db.collection('purchases').document(response_json["data"]["tx_ref"]).set(response_json["data"])

                    # Send notification
                    try:
                        message = messaging.Message(
                            notification=messaging.Notification(
                                title="Purchase Successful",
                                body=f"{response_json['data']['tx_ref']} Confirmed. You have successfully purchased {response_json['data']['amount']} Iki points. Your new Iki points balance is {new_points}. A transaction receipt has been sent to your email.",
                            ),
                            token=response_json["data"]["meta"]["fcm_token"],
                        )
                        messaging.send(message)
                        print("Notification sent successfully")
                    except Exception as e:
                        print(f"Error sending notification: {e}")

                    return Response({'status': 'success', 'points': new_points}, status=200)
                else:
                    return Response({'status': 'success', 'points': points_balance}, status=200)

            except Exception as e:
                print(e)
                return Response({'status': 'error', 'message': str(e)}, status=500)

        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=500)

class AppointmentBookingView(APIView):
    def post(self, request):
        """Webhook to handle Cal.com BOOKING_CREATED events."""
        # Only accept POST requests
        if request.method != "POST":
            return Response({"error": "Only POST requests are accepted"}, status=405)

        try:
            # Get the JSON data from the request
            webhook_data = request.data
            print(webhook_data)
            if not webhook_data:
                return Response({"error": "No JSON data provided"}, status=400)

            # Extract the 'body' section (assuming webhook_data is the payload directly)
            body = webhook_data
            if not body:
                return Response({"error": "No 'body' in webhook data"}, status=400)

            # Extract key booking details from the payload
            payload = body.get("payload", {})
            booking_id = payload.get("bookingId")
            event_title = payload.get("eventTitle")
            start_time = payload.get("startTime")
            end_time = payload.get("endTime")
            organizer = payload.get("organizer", {}).get("name")
            organizer_email = payload.get("organizer", {}).get("email")
            organizer_username = payload.get("organizer", {}).get("username")
            attendee = payload.get("attendees", [{}])[0].get("name")
            attendee_email = payload.get("attendees", [{}])[0].get("email")
            try:
                video_call_url = payload.get("metadata", {}).get("videoCallUrl")
            except Exception as e:
                print(f"Not a video meeting {str(e)}")
                video_call_url = "Physical attendance required"
            status = payload.get("status")

            # Log for debugging
            print(f"Received booking: {booking_id} - {event_title} for {attendee}")

            # Save to Firestore
            booking_doc = {
                "booking_id": booking_id,
                "event_title": event_title,
                "start_time": start_time,
                "end_time": end_time,
                "organizer": organizer,
                "organizer_email": organizer_email,
                "organizer_username": organizer_username,
                "attendee": attendee,
                "attendee_email": attendee_email,
                "video_call_url": video_call_url,
                "status": status,
                "created_at": body.get("createdAt")
            }

            db = firestore.client()

            # Search Firestore for a user with this email
            users_ref = db.collection("users").where("email", "==", attendee_email).limit(1)
            user_docs = users_ref.stream()

            user_id = None
            for doc in user_docs:
                user_data = doc.to_dict()
                user_id = user_data.get("id")  # Adjust field name if different
                print(f"Found user with email {attendee_email}, userId: {user_id}")

                # Reference the bookings document for this user
                user_doc_ref = db.collection("bookings").document(user_id)

                # Ensure the document exists with a timestamp
                user_doc_ref.set({
                    "last_updated": firestore.SERVER_TIMESTAMP
                }, merge=True)

                # Append the booking to an array field called 'bookings'
                user_doc_ref.set({
                    "bookings": firestore.ArrayUnion([booking_doc])
                }, merge=True)

                # Prepare success response
                response_data = {
                    "message": "Webhook processed successfully",
                    "booking_id": booking_id,
                    "event_title": event_title,
                    "attendee": attendee,
                    "video_call_url": video_call_url
                }
                return Response(response_data, status=200)

            if not user_id:
                print(f"No user found with email: {attendee_email}")
                # Store in a temporary collection for unclaimed bookings
                db.collection("unclaimed_bookings").add(booking_doc)
                return Response({
                    "message": "Booking stored temporarily - no owner found for email",
                    "booking_id": booking_id
                }, status=200)

        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            return Response({"error": "Internal server error"}, status=500)
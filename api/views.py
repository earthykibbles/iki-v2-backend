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

# Configure timezone and API key
nairobi_tz = pytz.timezone('Africa/Nairobi')
GOOGLE_API_KEY = "AIzaSyD9BptOSDadXqC2mA6Hn9PXOB2VXXaax5E"
FLUTTERWAVE_API_KEY = "FLWSECK-2670a3b04d04343235edbc819a34e978-194844cd018vt-X"

class GenerateContentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            prompt = request.data.get("prompt")
            schema = request.data.get('schema')

            schema_map = {
                "condition": ChronicCondition,
                "fitness": WorkoutPlanModel,
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
            prompt = "generate 5 workout plans that are versatile and great for different peoples."
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_id = request.user.id  # Assuming your User model has an 'id' field matching Firebase UID
            cost_points = request.data.get("costPoints")

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


class RechargePointsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_id = request.user.id
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
    authentication_classes = [JWTAuthentication]
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
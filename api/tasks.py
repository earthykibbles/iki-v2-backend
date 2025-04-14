from celery import shared_task
from google import genai
from firebase_admin import firestore, messaging
from datetime import datetime
import pytz
import json
from django.conf import settings
from mistralai import Mistral
from celery import Celery
import time


from api.models import (
    ChronicCondition, WorkoutPlanModel, Medicine, QuestionSchema,
    MindfulnessPlanModel, SymptomsSchema, TitleSchema, RecommendationSchema,
    WorkoutLanding, MindfulnessLanding, NutritionLanding, Interests
)
from meals.schemas import Nutrition

nairobi_tz = pytz.timezone('Africa/Nairobi')
GOOGLE_API_KEY = settings.GOOGLE_API_KEY

MISTRAL_API_KEY = settings.MISTRAL_API_KEY


@shared_task
def generate_content_task(prompt, schema):
    try:
        schema_map = {
            "condition": ChronicCondition,
            "fitness": WorkoutPlanModel,
            "medicine": Medicine,
            "onboarding": QuestionSchema,
            "mindfulness": MindfulnessPlanModel,
            "symptoms": SymptomsSchema,
            "title": TitleSchema,
            "mood": RecommendationSchema,
            "interests": Interests
        }
        model = schema_map.get(schema)
        if not model:
            return {'status': 'failed', 'error': 'Invalid schema'}

        # client = genai.Client(api_key=GOOGLE_API_KEY)
        # response = client.models.generate_content(
        #     model="gemini-2.5-pro-exp-03-25",
        #     contents=prompt,
        #     config={
        #         'response_mime_type': 'application/json',
        #         'response_schema': model
        #     },
        # )
        # result = json.loads(response.text)
        client = Mistral(api_key=MISTRAL_API_KEY)

        completion = client.chat.parse(
            model="ministral-8b-latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format = model,
        )

        event = completion.choices[0].message.model_dump_json()
        result = json.loads(json.loads(event)["content"])
        return {'status': 'completed', 'result': result}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}


@shared_task
def generate_fitness_landing_task():
    try:
        prompt = "generate 10 workout plans that are versatile and great for different peoples."
        # client = genai.Client(api_key=GOOGLE_API_KEY)
        # response = client.models.generate_content(
        #     model="gemini-2.5-pro-exp-03-25",
        #     contents=prompt,
        #     config={
        #         'response_mime_type': 'application/json',
        #         'response_schema': WorkoutLanding
        #     },
        # )
        # result = json.loads(response.text)
        client = Mistral(api_key=MISTRAL_API_KEY)

        completion = client.chat.parse(
            model="ministral-8b-latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format=WorkoutLanding,
        )

        event = completion.choices[0].message.model_dump_json()
        result = json.loads(json.loads(event)["content"])

        # Save to Firestore
        db = firestore.client()
        today = datetime.now(nairobi_tz).strftime('%Y%m%d')
        db.collection('fitness_landings').document(today).set(result)

        return {'status': 'completed', 'result': result}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}


@shared_task
def generate_mindfulness_landing_task():
    try:
        prompt = "generate 7 mindfulness exercises that are versatile and great for different peoples."
        # client = genai.Client(api_key=GOOGLE_API_KEY)
        # response = client.models.generate_content(
        #     model="gemini-2.5-pro-exp-03-25",
        #     contents=prompt,
        #     config={
        #         'response_mime_type': 'application/json',
        #         'response_schema': MindfulnessLanding
        #     },
        # )
        # result = json.loads(response.text)

        client = Mistral(api_key=MISTRAL_API_KEY)

        completion = client.chat.parse(
            model="ministral-8b-latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format=MindfulnessLanding,
        )

        event = completion.choices[0].message.model_dump_json()
        result = json.loads(json.loads(event)["content"])

        # Save to Firestore
        db = firestore.client()
        today = datetime.now(nairobi_tz).strftime('%Y%m%d')
        db.collection('mindfulness_landings').document(today).set(result)

        return {'status': 'completed', 'result': result}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}


@shared_task
def generate_nutrition_landing_task():
    try:
        prompt = "generate 10 different meals and exhaustively description of how to prepare them that are versatile and great for different peoples."
        # client = genai.Client(api_key=GOOGLE_API_KEY)
        # response = client.models.generate_content(
        #     model="gemini-2.5-pro-exp-03-25",
        #     contents=prompt,
        #     config={
        #         'response_mime_type': 'application/json',
        #         'response_schema': NutritionLanding
        #     },
        # )
        # result = json.loads(response.text)
        client = Mistral(api_key=MISTRAL_API_KEY)

        completion = client.chat.parse(
            model="ministral-8b-latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format=NutritionLanding,
        )

        event = completion.choices[0].message.model_dump_json()
        result = json.loads(json.loads(event)["content"])

        # Save to Firestore
        db = firestore.client()
        today = datetime.now(nairobi_tz).strftime('%Y%m%d')
        db.collection('nutrition_landings').document(today).set(result)

        return {'status': 'completed', 'result': result}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}


##############################################################################################
@shared_task
def process_call_event(data):
    receiver_id = data.get("receiverID")
    if not receiver_id:
        return "ReceiverID missing"

    # Fetch Firestore document for the receiver
    db = firestore.client()
    user_doc = db.collection("users").document(receiver_id).get()
    if not user_doc.exists:
        return f"User {receiver_id} not found"

    user_data = user_doc.to_dict()
    fcm_token = user_data.get("fcm_token")
    if not fcm_token:
        return f"FCM token not found for user {receiver_id}"

    # Build notification payload
    data_payload = {
        "type": "call",
        "call_details": data.get("sessionID"),
        "call_from": data.get("callerID"),
        "call_type": data.get("type_of_call")
    }

    # Create and send message
    message = messaging.Message(
        notification=messaging.Notification(
            title="Incoming Call",
            body="Call from Outside"
        ),
        data=data_payload,
        token=fcm_token
    )

    try:
        response = messaging.send(message)
        # Mark the call as notified in Firestore
        db.collection("calls").document(data["sessionID"]).update({"notified": True})
        return f"Notification sent successfully to {receiver_id}: {response}"
    except Exception as e:
        return f"Error sending notification: {e}"


@shared_task
def process_chat_message_notification(data):
    chat_id = data.get("chat_id")
    message_id = data.get("message_id")
    sender_uid = data.get("sender_uid")
    receiver_id = data.get("receiver_id")
    message_body = data.get("message_body")

    db = firestore.client()

    # Get chat participants
    chat_doc_ref = db.collection('chats').document(chat_id)
    chat_doc = chat_doc_ref.get()

    if not chat_doc.exists:
        return f"Chat {chat_id} not found"

    chat_data = chat_doc.to_dict()
    chat_people = chat_data.get("users", [])

    # Check who is the recipient (the one who is not the sender)
    if sender_uid == chat_people[0]:
        recipient_id = chat_people[1]
    elif sender_uid == chat_people[1]:
        recipient_id = chat_people[0]
    else:
        return "Sender is not in the chat participants"

    # Fetch recipient's FCM token
    recipient_doc_ref = db.collection('users').document(recipient_id)
    recipient_doc = recipient_doc_ref.get()

    if not recipient_doc.exists:
        return f"User {recipient_id} not found"

    recipient_data = recipient_doc.to_dict()
    fcm_token = recipient_data.get("fcm_token")
    if not fcm_token:
        return f"FCM token not found for user {recipient_id}"

    # Fetch sender's name
    sender_doc_ref = db.collection('users').document(sender_uid)
    sender_doc = sender_doc_ref.get()

    if not sender_doc.exists:
        return f"Sender {sender_uid} not found"

    sender_data = sender_doc.to_dict()
    firstname = sender_data.get("firstname")
    lastname = sender_data.get("lastname")

    # Build notification payload
    data_payload = {
        "type": "message",
        "message_from": sender_uid,
    }

    # Create notification
    message = messaging.Message(
        notification=messaging.Notification(
            title=f'{firstname} {lastname} sent a message',
            body=message_body,
        ),
        data=data_payload,  # Optional data payload
        token=fcm_token,
    )

    try:
        # Send the message
        response = messaging.send(message)
        print(f"Notification sent to {recipient_id}: {response}")

        # Mark message as notified in Firestore
        chat_doc_ref.collection('messages').document(message_id).update({"notified": True})

        return response
    except Exception as e:
        print(f"Error sending notification: {e}")
        return None

@shared_task
def process_friend_request_notification(data):
    user_id = data.get("user_id")
    friend_id = data.get("friend_id")

    # Initialize Firestore client
    db = firestore.client()

    # Get the FCM token of the friend
    doc_ref = db.collection('users').document(friend_id)
    doc = doc_ref.get()

    if not doc.exists:
        return f"User {friend_id} not found"

    user_data = doc.to_dict()
    fcm_token = user_data.get('fcm_token')
    if not fcm_token:
        return f"FCM token not found for {friend_id}"

    # Get sender's details
    sender_doc_ref = db.collection('users').document(user_id)
    sender_doc = sender_doc_ref.get()

    if not sender_doc.exists:
        return f"Sender {user_id} not found"

    sender_data = sender_doc.to_dict()
    firstname = sender_data['firstname']
    lastname = sender_data['lastname']
    username = sender_data['username']

    # Payload for notification
    data_payload = {
        "type": "friend_request",
        "request_from": user_id,
    }

    # Send notification to the friend
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title="New Friend Request",
                body=f"{firstname} {lastname} (@{username}) wants to be your friend.",
            ),
            data=data_payload,
            token=fcm_token,
        )

        response = messaging.send(message)
        print(f"Friend request notification sent: {response}")
        return response

    except Exception as e:
        print(f"Error sending notification: {e}")
        return None

@shared_task
def process_accept_friend_request_notification(data):
    user_id = data.get("user_id")
    friend_id = data.get("friend_id")

    # Initialize Firestore client
    db = firestore.client()

    # Check if the friend request exists
    partya_doc_ref = db.collection('users').document(friend_id).collection('friends').document(user_id)
    partya_doc = partya_doc_ref.get()

    if not partya_doc.exists:
        return f"No friend request from {friend_id} to {user_id}"

    # Set both users as friends
    try:
        # Update the status for both users
        partya_doc_ref.update({'friend_status': 'friends'})
        mine_doc_ref = db.collection('users').document(user_id).collection('friends').document(friend_id)
        mine_doc_ref.update({'friend_status': 'friends'})
        print(f"Friend status updated for {user_id} and {friend_id}")
    except Exception as e:
        print(f"Error updating friend status: {e}")
        return None

    # Get the FCM token of the friend
    doc_ref = db.collection('users').document(friend_id)
    doc = doc_ref.get()

    if not doc.exists:
        return f"User {friend_id} not found"

    user_data = doc.to_dict()
    fcm_token = user_data.get('fcm_token')
    if not fcm_token:
        return f"FCM token not found for {friend_id}"

    # Get sender's details
    sender_doc_ref = db.collection('users').document(user_id)
    sender_doc = sender_doc_ref.get()

    if not sender_doc.exists:
        return f"Sender {user_id} not found"

    sender_data = sender_doc.to_dict()
    firstname = sender_data['firstname']
    lastname = sender_data['lastname']
    username = sender_data['username']

    # Payload for notification
    data_payload = {
        "type": "friend_request_accepted",
        "request_from": user_id,
    }

    # Send notification to the friend
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title="You are now friends",
                body=f"{firstname} {lastname} (@{username}) is now your friend. Start chatting with them!",
            ),
            data=data_payload,
            token=fcm_token,
        )

        response = messaging.send(message)
        print(f"Friend request accepted notification sent: {response}")
        return response

    except Exception as e:
        print(f"Error sending notification: {e}")
        return None


@shared_task
def process_comment_event(data):
    post_id = data.get("post_id")
    comment_id = data.get("comment_id")

    db = firestore.client()

    # Get the post owner and FCM token
    post_ref = db.collection('posts').document(post_id)
    post_doc = post_ref.get()

    if not post_doc.exists:
        return f"Post {post_id} not found"

    post_data = post_doc.to_dict()
    owner_id = post_data['ownerId']
    fcm_token = db.collection('users').document(owner_id).get().to_dict()['fcm_token']

    # Get comment data
    comment_ref = db.collection('comments').document(post_id).collection('comments').document(comment_id)
    comment_doc = comment_ref.get()

    if not comment_doc.exists:
        return f"Comment {comment_id} not found"

    comment_data = comment_doc.to_dict()
    username = comment_data['username']
    user_id = comment_data['userId']
    comment_text = comment_data['comment']
    timestamp = comment_data['timestamp']

    # Data payload for notification
    data_payload = {
        "type": "comment",
        "post_id": post_id,
        "user_id": user_id
    }

    # Send notification to post owner
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=f"{username} commented",
                body=f"{comment_text} on {timestamp}",
            ),
            data=data_payload,
            token=fcm_token,
        )

        response = messaging.send(message)
        print(f"Comment notification sent: {response}")
        return response

    except Exception as e:
        print(f"Error sending notification: {e}")
        return None

@shared_task
def process_appointment_set_event(data):
    booker = data.get("booker")
    bookee = data.get("bookee")
    appointment_time = data.get("time")
    appointment_date = data.get("date")
    reminder = data.get("reminder")

    db = firestore.client()

    # Get FCM token for booker
    booker_ref = db.collection('users').document(booker)
    booker_doc = booker_ref.get()

    if not booker_doc.exists:
        return f"User {booker} not found"

    booker_data = booker_doc.to_dict()
    fcm_token = booker_data['fcm_token']

    # Data payload for appointment
    data_payload = {
        "type": "appointment",
        "appointment_with": bookee,
        "appointment_time": appointment_time,
        "appointment_date": appointment_date,
        "reminder": reminder
    }

    # Send appointment confirmation to booker
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title="Appointment Confirmation",
                body="Your appointment has been received and scheduled. You will receive a reminder and another confirmation as it approaches.",
            ),
            data=data_payload,
            token=fcm_token,
        )

        response = messaging.send(message)
        print(f"Appointment notification sent: {response}")
        return response

    except Exception as e:
        print(f"Error sending notification: {e}")
        return None


@shared_task
def schedule_status_deletion(data):
    status_id = data.get("status_id")
    now = time.time()  # Get the current timestamp in seconds

    # Set the deletion time to 24 hours from now
    delete_time = now + 86400  # 24 hours = 86400 seconds

    # Save the status with the timestamp for deletion in Firestore
    db = firestore.client()
    status_ref = db.collection("status").document(status_id)
    status_ref.update({"delete_at": delete_time})

    print(f"Status {status_id} scheduled for deletion at {delete_time}")
    return f"Scheduled {status_id} for deletion"


from iki.celery import app

@app.task
def delete_expired_statuses():
    db = firestore.client()
    now = time.time()  # Get the current timestamp

    # Query for statuses with a `delete_at` field and check if it has expired
    statuses_ref = db.collection("status")
    expired_statuses = statuses_ref.where("delete_at", "<", now).stream()

    for status in expired_statuses:
        status_ref = db.collection("status").document(status.id)
        status_ref.delete()
        print(f"Deleted expired status {status.id}")
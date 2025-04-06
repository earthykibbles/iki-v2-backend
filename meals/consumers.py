import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iki.settings")

django.setup()  # Ensure Django apps are initialized before usage

import json
import gzip
from channels.generic.websocket import AsyncWebsocketConsumer

from rest_framework_simplejwt.tokens import AccessToken
from .utils import process_image

class ImageProcessingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract JWT token from headers
        token = self.scope["query_string"].decode().split("token=")[-1] if "token=" in self.scope["query_string"].decode() else None

        if not token:
            await self.close()
            return

        try:
            decoded_token = AccessToken(token)
            self.user_id = decoded_token["user_id"]  # Store the user ID
            print(f"User {self.user_id} connected")
            await self.accept()
        except Exception as e:
            print(f"Invalid token: {e}")
            await self.close()

        self.prompt = None
        self.image_data = None

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                prompt_data = json.loads(text_data)
                self.prompt = prompt_data.get("prompt", "")
                print(f"User {self.user_id} sent prompt: {self.prompt}")
            except json.JSONDecodeError:
                print(f"User {self.user_id} sent invalid JSON")

        elif bytes_data:
            try:
                self.image_data = gzip.decompress(bytes_data)
                print(f"User {self.user_id} uploaded an image!")

                async for partial_result in process_image(self.image_data, self.prompt):
                    await self.send(text_data=json.dumps({"user": self.user_id, "result": partial_result}))

                await self.close()
            except Exception as e:
                print(f"Error processing image for user {self.user_id}: {e}")
                await self.send(text_data=json.dumps({"error": str(e)}))
                await self.close()

    async def disconnect(self, close_code):
        print(f"User {self.user_id} disconnected with code: {close_code}")
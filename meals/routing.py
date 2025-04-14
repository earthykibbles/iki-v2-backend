from django.urls import re_path, path
from api.consumers import ImageProcessingConsumer

websocket_urlpatterns = [
    re_path(r"ws/process-image/$", ImageProcessingConsumer.as_asgi()),
]
from django.http import JsonResponse
import socket


def home(request):
    return JsonResponse({
        "application": " DevOps Django AWS Project by @st-sachin bro ec1111",
        "status": "running",
        "server": socket.gethostname(),
        "message": "Django application is working"
    })


def health(request):
    return JsonResponse({
        "status": "healthy",
        "server": socket.gethostname()
    })
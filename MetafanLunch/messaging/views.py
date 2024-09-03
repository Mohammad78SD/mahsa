from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render
from .models import WebPushSubscription, Notification
import json

def home(request):
    return render(request, 'messaging/home.html')

@csrf_exempt
def save_subscription(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        WebPushSubscription.objects.create(subscription_json=data)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=405)

def get_vapid_key(request):
    vapid_key = settings.VAPID_PUBLIC_KEY
    if isinstance(vapid_key, (list, tuple)):
        vapid_key = vapid_key[0]
    if isinstance(vapid_key, bytes):
        vapid_key = vapid_key.decode('utf-8')
    return JsonResponse({'publicKey': vapid_key})


def message_list(request):
    messages = Notification.objects.all().filter().order_by('-created_at')
    print(f"messages: {messages}")
    return render(request, 'messaging/messages-list.html', {'messages' : messages})
    
    
    
def offline(request):
    return render(request, 'offline.html')
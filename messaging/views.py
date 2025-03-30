from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render, redirect
from .models import WebPushSubscription, Notification, SharedFile
import json
from django.contrib.auth.decorators import login_required
from lunch.models import CustomUser as User

from django.contrib import messages



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


@login_required
def send_file(request):
    print("In send file view")
    if not request.user.is_file:
        return HttpResponseForbidden("You do not have permission to access this feature.")

    if request.method == 'POST':
        # Extract file and recipients from the request
        file = request.FILES.get('file')
        name = request.POST.get('name', '')
        recipients_ids = request.POST.get('recipients', '').split(',')
        
        # Convert recipient IDs to integers and filter out any invalid IDs
        recipients_ids = [int(id) for id in recipients_ids if id.isdigit()]

        # Create a new SharedFile instance
        shared_file = SharedFile(sender=request.user, name=name, file=file)

        # Save the shared file instance
        shared_file.save()

        # Set the recipients using the list of IDs
        shared_file.recipients.set(recipients_ids)
        messages.success(request, "فایل شما با موفقیت ارسال شد!")
        return redirect('file_list')  # Redirect to a list of sent/received files
    else:
        # Get all users for the dropdown
        users = User.objects.all()
        return render(request, 'messaging/send_file.html', {'users': users})


@login_required
def file_list(request):
    if not request.user.is_file:
        return HttpResponseForbidden("You do not have permission to access this feature.")
    received_files = request.user.received_files.all().order_by('-created_at')
    return render(request, 'messaging/file_list.html', {'received_files': received_files})


@login_required
def download_file(request, file_id):
    if not request.user.is_file:
        return HttpResponseForbidden("شما به این قابلیت دسترسی ندارید.")

    try:
        shared_file = SharedFile.objects.get(id=file_id, recipients=request.user) # Ensure user is a recipient
        shared_file.seen = True
        shared_file.save()
    except SharedFile.DoesNotExist:
        raise Http404("File not found.")
    
    # Serve the file using Django's FileResponse
    from django.http import FileResponse
    response = FileResponse(shared_file.file, as_attachment=True, filename=shared_file.file.name)  # Use original filename
    return response
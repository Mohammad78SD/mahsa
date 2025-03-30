from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.message_list, name='messages_list'),
    path('send/', views.send_file, name='send_file'),
    path('files/', views.file_list, name='file_list'),
    path('download/<int:file_id>/', views.download_file, name='download_file'),
]

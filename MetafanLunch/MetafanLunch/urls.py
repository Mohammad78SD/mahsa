from django.urls import include, path
from django.contrib import admin
from django.views.generic.base import TemplateView

admin.site.site_header = 'پنل مدیریت متافن'
admin.site.index_title = 'مدیریت متافن'
urlpatterns = [
    path('lunch/', include('lunch.urls')),
    path('admin/', admin.site.urls),
    path('',TemplateView.as_view(template_name='index.html'), name='home'),
    path('surveys/', include('surveys.urls')),
    path('dashboard',TemplateView.as_view(template_name='dashboard.html'), name='dashboard')
]
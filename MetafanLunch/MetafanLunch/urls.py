from django.urls import include, path

from django.contrib import admin
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.conf.urls.static import static
from messaging import views

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    login_url = '/lunch/login/'

admin.site.site_header = 'پنل مدیریت متافن'
admin.site.index_title = 'مدیریت متافن'



urlpatterns = [
    
    path('lunch/', include('lunch.urls')),
    path('admin/', admin.site.urls),
    path('',TemplateView.as_view(template_name='index.html'), name='home'),
    path('surveys/', include('surveys.urls')),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    
    path('home/', views.home, name='home'),
    path('save-subscription/', views.save_subscription, name='save_subscription'),
    path('get-vapid-key/', views.get_vapid_key, name='get_vapid_key'),
    path('messages/', include('messaging.urls')),
    path('offline/', views.offline, name='offline'),
        
    path('', include('pwa.urls')),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
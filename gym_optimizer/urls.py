from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # Authentication URLs
    path('accounts/', include('allauth.urls')),  # Django Allauth URLs (includes Google OAuth)
    
    # App URLs
    path('users/', include('users.urls')),
    path('workouts/', include('workouts.urls')),
    path('progress/', include('progress.urls')),
    path('nutrition/', include('nutrition.urls')),
    
    # API endpoints
    path('api/', include('api.urls')),
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
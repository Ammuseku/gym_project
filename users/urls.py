from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('register/', views.register, name='register'),
    path('connect/google-fit/', views.connect_google_fit, name='connect_google_fit'),
    path('disconnect/google-fit/', views.disconnect_google_fit, name='disconnect_google_fit'),
    path('connect/apple-health/', views.connect_apple_health, name='connect_apple_health'),
    path('disconnect/apple-health/', views.disconnect_apple_health, name='disconnect_apple_health'),

]
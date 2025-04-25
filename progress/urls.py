from django.urls import path
from . import views

urlpatterns = [
    # Main progress tracking pages
    path('', views.progress_tracking, name='progress_tracking'),
    path('analytics/', views.analytics, name='analytics'),

    # Body metrics logging and history
    path('log-progress/', views.log_progress, name='log_progress'),
    path('metrics-history/', views.metrics_history, name='metrics_history'),
    path('delete-metric/<int:pk>/', views.delete_metric, name='delete_metric'),

    # Workout logging and history
    path('log-workout/', views.log_workout, name='log_workout'),
    path('workout-history/', views.workout_history, name='workout_history'),
    path('workout/<int:pk>/', views.workout_detail, name='workout_detail'),
    path('delete-workout/<int:pk>/', views.delete_workout, name='delete_workout'),

    # Goals management
    path('goals/', views.goals, name='goals'),
    path('goals/create/', views.create_goal, name='create_goal'),
    path('goals/edit/<int:pk>/', views.edit_goal, name='edit_goal'),
    path('goals/delete/<int:pk>/', views.delete_goal, name='delete_goal'),

    # Milestones management
    path('milestones/', views.milestones, name='milestones'),
    path('milestones/create/', views.create_milestone, name='create_milestone'),
    path('milestones/delete/<int:pk>/', views.delete_milestone, name='delete_milestone'),

    # API endpoints for charts
    path('api/chart-data/', views.get_chart_data, name='get_chart_data'),
]
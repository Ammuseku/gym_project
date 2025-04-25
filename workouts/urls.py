from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),

    # Exercise library
    path('exercises/', views.exercise_library, name='exercise_library'),
    path('exercises/<int:pk>/', views.exercise_detail, name='exercise_detail'),

    # Workout plans
    path('plans/', views.workout_plans, name='workout_plans'),
    path('plans/<int:pk>/', views.plan_detail, name='plan_detail'),
    path('plans/create/', views.create_plan, name='create_plan'),
    path('plans/<int:pk>/edit/', views.edit_plan, name='edit_plan'),
    path('plans/<int:pk>/delete/', views.delete_plan, name='delete_plan'),
    path('plans/<int:pk>/follow/', views.follow_plan, name='follow_plan'),
    path('plans/<int:pk>/unfollow/', views.unfollow_plan, name='unfollow_plan'),

    # AI plan generation
    path('plans/generate-ai/', views.generate_ai_plan, name='generate_ai_plan'),

    # Schedule
    path('schedule/', views.schedule, name='schedule'),
    path('schedule/add/', views.schedule_workout, name='schedule_workout'),

    # Workout logging
    path('log/<int:schedule_id>/', views.log_workout, name='log_workout'),
    path('mark-completed/<int:schedule_id>/', views.mark_workout_completed, name='mark_workout_completed'),
]
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.nutrition_dashboard, name='nutrition'),

    # Meal plans
    path('meal-plans/', views.meal_plans, name='meal_plans'),
    path('meal-plans/<int:pk>/', views.meal_plan_detail, name='meal_plan_detail'),
    path('meal-plans/create/', views.create_meal_plan, name='create_meal_plan'),
    path('meal-plans/<int:pk>/edit/', views.edit_meal_plan, name='edit_meal_plan'),
    path('meal-plans/<int:pk>/delete/', views.delete_meal_plan, name='delete_meal_plan'),
    path('meal-plans/<int:pk>/activate/', views.activate_meal_plan, name='activate_meal_plan'),

    # AI meal plan generation
    path('meal-plans/generate-ai/', views.generate_ai_meal_plan, name='generate_ai_meal_plan'),

    # Meals
    path('meal-plans/<int:plan_id>/add-meal/', views.add_meal, name='add_meal'),
    path('meals/<int:pk>/', views.meal_detail, name='meal_detail'),
    path('meals/<int:pk>/edit/', views.edit_meal, name='edit_meal'),
    path('meals/<int:pk>/delete/', views.delete_meal, name='delete_meal'),

    # Meal items
    path('meals/<int:meal_id>/add-food/', views.add_food_to_meal, name='add_food_to_meal'),
    path('meal-items/<int:pk>/edit/', views.edit_meal_item, name='edit_meal_item'),
    path('meal-items/<int:pk>/delete/', views.delete_meal_item, name='delete_meal_item'),

    # Food library
    path('foods/', views.food_library, name='food_library'),
    path('foods/add/', views.add_food, name='add_food'),
    path('foods/<int:pk>/', views.food_detail, name='food_detail'),
    path('foods/<int:pk>/edit/', views.edit_food, name='edit_food'),
    path('foods/<int:pk>/delete/', views.delete_food, name='delete_food'),

    # Spoonacular API integration
    path('foods/search/', views.search_spoonacular, name='search_spoonacular'),
    path('foods/add-spoonacular/<int:spoonacular_id>/', views.add_spoonacular_food, name='add_spoonacular_food'),

    # Nutrition logging
    path('log/', views.log_nutrition, name='log_nutrition'),
    path('logs/', views.nutrition_logs, name='nutrition_logs'),
    path('logs/<int:pk>/delete/', views.delete_nutrition_log, name='delete_nutrition_log'),
]
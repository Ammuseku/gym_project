from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.UserProfileViewSet, basename='profile')
router.register(r'muscle-groups', views.MuscleGroupViewSet)
router.register(r'exercises', views.ExerciseViewSet)
router.register(r'workout-plans', views.WorkoutPlanViewSet, basename='workout-plan')
router.register(r'plan-exercises', views.PlanExerciseViewSet, basename='plan-exercise')
router.register(r'user-workout-plans', views.UserWorkoutPlanViewSet, basename='user-workout-plan')
router.register(r'user-plan-exercises', views.UserPlanExerciseViewSet, basename='user-plan-exercise')
router.register(r'workout-schedules', views.WorkoutScheduleViewSet, basename='workout-schedule')
router.register(r'body-metrics', views.BodyMetricsViewSet, basename='body-metrics')
router.register(r'workout-logs', views.WorkoutLogViewSet, basename='workout-log')
router.register(r'goals', views.GoalViewSet, basename='goal')
router.register(r'milestones', views.MilestoneViewSet, basename='milestone')
router.register(r'food-items', views.FoodItemViewSet, basename='food-item')
router.register(r'meal-plans', views.MealPlanViewSet, basename='meal-plan')
router.register(r'meals', views.MealViewSet, basename='meal')
router.register(r'meal-items', views.MealItemViewSet, basename='meal-item')
router.register(r'nutrition-logs', views.DailyNutritionLogViewSet, basename='nutrition-log')

urlpatterns = [
    path('', include(router.urls)),
    path('me/', views.current_user_profile, name='current-user'),
    #path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from users.models import UserProfile
from workouts.models import (
    MuscleGroup, Exercise, WorkoutPlan, PlanExercise,
    UserWorkoutPlan, UserPlanExercise, WorkoutSchedule
)
from progress.models import (
    BodyMetrics, WorkoutLog, Goal, Milestone
)
from nutrition.models import (
    FoodItem, MealPlan, Meal, MealItem, DailyNutritionLog
)
from .serializers import (
    UserSerializer, UserProfileSerializer,
    MuscleGroupSerializer, ExerciseSerializer,
    WorkoutPlanSerializer, PlanExerciseSerializer,
    UserWorkoutPlanSerializer, UserPlanExerciseSerializer,
    WorkoutScheduleSerializer, BodyMetricsSerializer,
    WorkoutLogSerializer, GoalSerializer, MilestoneSerializer,
    FoodItemSerializer, MealPlanSerializer, MealSerializer,
    MealItemSerializer, DailyNutritionLogSerializer
)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing users"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserProfileViewSet(viewsets.ModelViewSet):
    """API endpoint for user profiles"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only the current user's profile"""
        return UserProfile.objects.filter(user=self.request.user)


class MuscleGroupViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for muscle groups"""
    queryset = MuscleGroup.objects.all()
    serializer_class = MuscleGroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for exercises"""
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter exercises based on query parameters"""
        queryset = Exercise.objects.all()

        # Filter by muscle group
        muscle_group = self.request.query_params.get('muscle_group')
        if muscle_group:
            queryset = queryset.filter(muscle_group__id=muscle_group)

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by compound exercises
        is_compound = self.request.query_params.get('is_compound')
        if is_compound:
            is_compound = is_compound.lower() == 'true'
            queryset = queryset.filter(is_compound=is_compound)

        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset


class WorkoutPlanViewSet(viewsets.ModelViewSet):
    """API endpoint for workout plans"""
    serializer_class = WorkoutPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return plans created by the user and public plans"""
        user = self.request.user
        return WorkoutPlan.objects.filter(created_by=user) | WorkoutPlan.objects.filter(is_public=True)

    def perform_create(self, serializer):
        """Set the current user as the creator"""
        serializer.save(created_by=self.request.user)


class PlanExerciseViewSet(viewsets.ModelViewSet):
    """API endpoint for plan exercises"""
    serializer_class = PlanExerciseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return exercises for plans created by the user"""
        user = self.request.user
        return PlanExercise.objects.filter(workout_plan__created_by=user)


class UserWorkoutPlanViewSet(viewsets.ModelViewSet):
    """API endpoint for user workout plans"""
    serializer_class = UserWorkoutPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return workout plans assigned to the user"""
        return UserWorkoutPlan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the current user"""
        serializer.save(user=self.request.user)


class UserPlanExerciseViewSet(viewsets.ModelViewSet):
    """API endpoint for user exercise logs"""
    serializer_class = UserPlanExerciseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return exercise logs for the user"""
        return UserPlanExercise.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the current user"""
        serializer.save(user=self.request.user)


class WorkoutScheduleViewSet(viewsets.ModelViewSet):
    """API endpoint for workout schedules"""
    serializer_class = WorkoutScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return schedules for the user"""
        return WorkoutSchedule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the current user"""
        serializer.save(user=self.request.user)


class BodyMetricsViewSet(viewsets.ModelViewSet):
    """API endpoint for body metrics"""
    serializer_class = BodyMetricsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return metrics for the user"""
        return BodyMetrics.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the current user"""
        serializer.save(user=self.request.user)


class WorkoutLogViewSet(viewsets.ModelViewSet):
    """API endpoint for workout logs"""
    serializer_class = WorkoutLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return logs for the user"""
        return WorkoutLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the current user"""
        serializer.save(user=self.request.user)


class GoalViewSet(viewsets.ModelViewSet):
    """API endpoint for goals"""
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return goals for the user"""
        return Goal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the current user"""
        serializer.save(user=self.request.user)


class MilestoneViewSet(viewsets.ModelViewSet):
    """API endpoint for milestones"""
    serializer_class = MilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return milestones for the user"""
        return Milestone.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the current user"""
        serializer.save(user=self.request.user)


class FoodItemViewSet(viewsets.ModelViewSet):
    """API endpoint for food items"""
    serializer_class = FoodItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return all food items and user-created ones"""
        user = self.request.user
        return FoodItem.objects.filter(is_user_created=False) | FoodItem.objects.filter(created_by=user)

    def perform_create(self, serializer):
        """Set the current user as creator and mark as user-created"""
        serializer.save(created_by=self.request.user, is_user_created=True)


class MealPlanViewSet(viewsets.ModelViewSet):
    """API endpoint for meal plans"""
    serializer_class = MealPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return meal plans for the user"""
        return MealPlan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the current user"""
        serializer.save(user=self.request.user)


class MealViewSet(viewsets.ModelViewSet):
    """API endpoint for meals"""
    serializer_class = MealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return meals from the user's meal plans"""
        return Meal.objects.filter(meal_plan__user=self.request.user)


class MealItemViewSet(viewsets.ModelViewSet):
    """API endpoint for meal items"""
    serializer_class = MealItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return meal items from the user's meals"""
        return MealItem.objects.filter(meal__meal_plan__user=self.request.user)


class DailyNutritionLogViewSet(viewsets.ModelViewSet):
    """API endpoint for nutrition logs"""
    serializer_class = DailyNutritionLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return nutrition logs for the user"""
        return DailyNutritionLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the current user"""
        serializer.save(user=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user_profile(request):
    """Get the current user's profile"""
    user = request.user
    serializer = UserSerializer(user)
    profile_serializer = UserProfileSerializer(user.profile)

    # Combine user and profile data
    data = serializer.data
    data['profile'] = profile_serializer.data

    return Response(data)
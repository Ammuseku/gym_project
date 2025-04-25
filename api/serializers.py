from rest_framework import serializers
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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        exclude = ['user']
        read_only_fields = ['created_at', 'updated_at']


class MuscleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MuscleGroup
        fields = '__all__'


class ExerciseSerializer(serializers.ModelSerializer):
    muscle_group_name = serializers.ReadOnlyField(source='muscle_group.name')

    class Meta:
        model = Exercise
        fields = '__all__'


class WorkoutPlanSerializer(serializers.ModelSerializer):
    created_by_username = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = WorkoutPlan
        fields = '__all__'
        read_only_fields = ['created_by', 'created_by_username', 'created_at', 'updated_at']


class PlanExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.ReadOnlyField(source='exercise.name')
    day_name = serializers.ReadOnlyField(source='get_day_of_week_display')

    class Meta:
        model = PlanExercise
        fields = '__all__'


class UserWorkoutPlanSerializer(serializers.ModelSerializer):
    plan_name = serializers.ReadOnlyField(source='workout_plan.name')

    class Meta:
        model = UserWorkoutPlan
        fields = '__all__'
        read_only_fields = ['user']


class UserPlanExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.ReadOnlyField(source='plan_exercise.exercise.name')

    class Meta:
        model = UserPlanExercise
        fields = '__all__'
        read_only_fields = ['user']


class WorkoutScheduleSerializer(serializers.ModelSerializer):
    plan_name = serializers.ReadOnlyField(source='workout_plan.name')
    day_name = serializers.ReadOnlyField(source='get_day_of_week_display')

    class Meta:
        model = WorkoutSchedule
        fields = '__all__'
        read_only_fields = ['user']


class BodyMetricsSerializer(serializers.ModelSerializer):
    metric_type_name = serializers.ReadOnlyField(source='get_metric_type_display')

    class Meta:
        model = BodyMetrics
        fields = '__all__'
        read_only_fields = ['user']


class WorkoutLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutLog
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class GoalSerializer(serializers.ModelSerializer):
    goal_type_name = serializers.ReadOnlyField(source='get_goal_type_display')
    status_name = serializers.ReadOnlyField(source='get_status_display')
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ['user']

    def get_progress(self, obj):
        return obj.get_progress_percentage()


class MilestoneSerializer(serializers.ModelSerializer):
    exercise_name = serializers.ReadOnlyField(source='exercise.name', default=None)

    class Meta:
        model = Milestone
        fields = '__all__'
        read_only_fields = ['user']


class FoodItemSerializer(serializers.ModelSerializer):
    macros_ratio = serializers.ReadOnlyField()

    class Meta:
        model = FoodItem
        fields = '__all__'
        read_only_fields = ['created_by', 'is_user_created', 'created_at', 'updated_at']


class MealPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealPlan
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class MealSerializer(serializers.ModelSerializer):
    meal_type_name = serializers.ReadOnlyField(source='get_meal_type_display')

    class Meta:
        model = Meal
        fields = '__all__'


class MealItemSerializer(serializers.ModelSerializer):
    food_name = serializers.ReadOnlyField(source='food_item.name')
    calories = serializers.SerializerMethodField()
    protein = serializers.SerializerMethodField()
    carbs = serializers.SerializerMethodField()
    fat = serializers.SerializerMethodField()

    class Meta:
        model = MealItem
        fields = '__all__'

    def get_calories(self, obj):
        return obj.get_calories()

    def get_protein(self, obj):
        return obj.get_protein()

    def get_carbs(self, obj):
        return obj.get_carbs()

    def get_fat(self, obj):
        return obj.get_fat()


class DailyNutritionLogSerializer(serializers.ModelSerializer):
    calories_percentage = serializers.SerializerMethodField()
    protein_percentage = serializers.SerializerMethodField()
    carbs_percentage = serializers.SerializerMethodField()
    fat_percentage = serializers.SerializerMethodField()

    class Meta:
        model = DailyNutritionLog
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_calories_percentage(self, obj):
        return obj.get_calories_percentage()

    def get_protein_percentage(self, obj):
        return obj.get_protein_percentage()

    def get_carbs_percentage(self, obj):
        return obj.get_carbs_percentage()

    def get_fat_percentage(self, obj):
        return obj.get_fat_percentage()
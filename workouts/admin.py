from django.contrib import admin
from .models import (
    MuscleGroup, Exercise, WorkoutPlan, PlanExercise,
    UserWorkoutPlan, UserPlanExercise, WorkoutSchedule
)


class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_exercise_count')
    search_fields = ('name',)


class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'muscle_group', 'difficulty', 'category', 'is_compound')
    list_filter = ('muscle_group', 'difficulty', 'category', 'is_compound')
    search_fields = ('name', 'description', 'equipment_needed')
    filter_horizontal = ('secondary_muscle_groups',)


class PlanExerciseInline(admin.TabularInline):
    model = PlanExercise
    extra = 1
    autocomplete_fields = ['exercise']


class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'goal', 'intensity', 'duration_weeks', 'created_by', 'is_public')
    list_filter = ('goal', 'intensity', 'is_public')
    search_fields = ('name', 'description')
    inlines = [PlanExerciseInline]


class UserWorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'workout_plan', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date')
    search_fields = ('user__username', 'workout_plan__name')
    date_hierarchy = 'start_date'


class UserPlanExerciseAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_exercise_name', 'date', 'weight', 'completed_sets', 'completed_reps', 'completed')
    list_filter = ('completed', 'date', 'perceived_difficulty')
    search_fields = ('user__username', 'plan_exercise__exercise__name')
    date_hierarchy = 'date'

    def get_exercise_name(self, obj):
        return obj.plan_exercise.exercise.name

    get_exercise_name.short_description = 'Exercise'
    get_exercise_name.admin_order_field = 'plan_exercise__exercise__name'


class WorkoutScheduleAdmin(admin.ModelAdmin):
    list_display = ('user', 'workout_plan', 'date', 'day_of_week', 'start_time', 'end_time', 'completed')
    list_filter = ('day_of_week', 'completed', 'notification_sent')
    search_fields = ('user__username', 'workout_plan__name')
    date_hierarchy = 'date'


admin.site.register(MuscleGroup, MuscleGroupAdmin)
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(WorkoutPlan, WorkoutPlanAdmin)
admin.site.register(UserWorkoutPlan, UserWorkoutPlanAdmin)
admin.site.register(UserPlanExercise, UserPlanExerciseAdmin)
admin.site.register(WorkoutSchedule, WorkoutScheduleAdmin)
from django.contrib import admin
from .models import BodyMetrics, WorkoutLog, Goal, Milestone

class BodyMetricsAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'metric_type', 'value')
    list_filter = ('metric_type', 'date')
    search_fields = ('user__username', 'notes')
    date_hierarchy = 'date'

class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'workout_name', 'duration', 'calories_burned')
    list_filter = ('date',)
    search_fields = ('user__username', 'workout_name', 'notes')
    date_hierarchy = 'date'

class GoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'goal_type', 'target_date', 'status')
    list_filter = ('goal_type', 'status', 'target_date')
    search_fields = ('user__username', 'title', 'description')
    date_hierarchy = 'target_date'

class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'date_achieved', 'exercise')
    list_filter = ('date_achieved',)
    search_fields = ('user__username', 'title', 'description')
    date_hierarchy = 'date_achieved'

admin.site.register(BodyMetrics, BodyMetricsAdmin)
admin.site.register(WorkoutLog, WorkoutLogAdmin)
admin.site.register(Goal, GoalAdmin)
admin.site.register(Milestone, MilestoneAdmin)
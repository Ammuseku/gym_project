from django.contrib import admin
from .models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'age', 'fitness_level', 'primary_goal', 'bmi', 'get_bmi_category')
    list_filter = ('gender', 'fitness_level', 'primary_goal')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('bmi', 'get_bmi_category', 'age')
    fieldsets = (
        (None, {
            'fields': ('user', 'avatar')
        }),
        ('Personal Information', {
            'fields': ('gender', 'birthdate', 'height', 'weight', 'bmi', 'get_bmi_category')
        }),
        ('Fitness Profile', {
            'fields': ('fitness_level', 'primary_goal', 'injuries', 'medical_conditions')
        }),
        ('Preferences', {
            'fields': ('weight_unit', 'receive_reminders', 'reminder_time', 'phone_number')
        }),
        ('Integrations', {
            'fields': ('google_fit_connected', 'apple_health_connected')
        }),
    )

admin.site.register(UserProfile, UserProfileAdmin)
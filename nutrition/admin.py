from django.contrib import admin
from .models import FoodItem, MealPlan, Meal, MealItem, DailyNutritionLog

class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories', 'protein', 'carbs', 'fat', 'is_user_created')
    list_filter = ('is_user_created',)
    search_fields = ('name', 'description')
    ordering = ('name',)

class MealItemInline(admin.TabularInline):
    model = MealItem
    extra = 1

class MealAdmin(admin.ModelAdmin):
    list_display = ('meal_plan', 'date', 'meal_type', 'get_total_calories')
    list_filter = ('meal_type', 'date')
    search_fields = ('meal_plan__name', 'name')
    date_hierarchy = 'date'
    inlines = [MealItemInline]

class MealPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'goal', 'calories_target', 'is_active', 'is_ai_generated')
    list_filter = ('goal', 'is_active', 'is_ai_generated')
    search_fields = ('name', 'user__username')
    date_hierarchy = 'created_at'

class DailyNutritionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'calories_consumed', 'protein_consumed', 'carbs_consumed', 'fat_consumed', 'is_cheat_day')
    list_filter = ('date', 'is_cheat_day')
    search_fields = ('user__username', 'notes')
    date_hierarchy = 'date'

admin.site.register(FoodItem, FoodItemAdmin)
admin.site.register(MealPlan, MealPlanAdmin)
admin.site.register(Meal, MealAdmin)
admin.site.register(DailyNutritionLog, DailyNutritionLogAdmin)
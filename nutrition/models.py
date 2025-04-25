from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class FoodItem(models.Model):
    """Model representing individual food items with nutritional information"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    serving_size = models.CharField(max_length=50)
    calories = models.PositiveIntegerField()
    protein = models.FloatField(help_text="Protein in grams")
    carbs = models.FloatField(help_text="Carbohydrates in grams")
    fat = models.FloatField(help_text="Fat in grams")
    fiber = models.FloatField(help_text="Fiber in grams", default=0)
    sugar = models.FloatField(help_text="Sugar in grams", default=0)

    # Spoonacular API fields
    external_id = models.CharField(max_length=100, blank=True, help_text="ID from external API")
    image_url = models.URLField(blank=True)

    # Added by users or system
    is_user_created = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_foods')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def macros_ratio(self):
        """Calculate macronutrient ratio (protein/carbs/fat)"""
        total = self.protein + self.carbs + self.fat
        if total == 0:
            return "0/0/0"

        protein_pct = int((self.protein / total) * 100)
        carbs_pct = int((self.carbs / total) * 100)
        fat_pct = int((self.fat / total) * 100)

        return f"{protein_pct}/{carbs_pct}/{fat_pct}"


class MealPlan(models.Model):
    """Model representing a meal plan for a user"""
    GOAL_CHOICES = (
        ('weight_loss', 'Weight Loss'),
        ('maintenance', 'Maintenance'),
        ('muscle_gain', 'Muscle Gain'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    calories_target = models.PositiveIntegerField()
    protein_target = models.PositiveIntegerField(help_text="Target protein in grams")
    carbs_target = models.PositiveIntegerField(help_text="Target carbs in grams")
    fat_target = models.PositiveIntegerField(help_text="Target fat in grams")

    # AI generated or manually created
    is_ai_generated = models.BooleanField(default=False)

    # Active dates
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    def get_daily_meals(self, day=None):
        """Get meals for a specific day, defaults to today"""
        if day is None:
            day = timezone.now().date()

        return Meal.objects.filter(
            meal_plan=self,
            date=day
        ).order_by('meal_type')

    def get_total_calories(self, day=None):
        """Calculate total calories for a day"""
        daily_meals = self.get_daily_meals(day)
        total = 0

        for meal in daily_meals:
            meal_items = MealItem.objects.filter(meal=meal)
            for item in meal_items:
                total += item.food_item.calories * item.servings

        return total

    def get_macros(self, day=None):
        """Calculate total macronutrients for a day"""
        daily_meals = self.get_daily_meals(day)
        protein = 0
        carbs = 0
        fat = 0

        for meal in daily_meals:
            meal_items = MealItem.objects.filter(meal=meal)
            for item in meal_items:
                protein += item.food_item.protein * item.servings
                carbs += item.food_item.carbs * item.servings
                fat += item.food_item.fat * item.servings

        return {
            'protein': protein,
            'carbs': carbs,
            'fat': fat
        }


class Meal(models.Model):
    """Model representing a meal within a meal plan"""
    MEAL_TYPES = (
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
        ('pre_workout', 'Pre-Workout'),
        ('post_workout', 'Post-Workout'),
    )

    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='meals')
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    date = models.DateField(default=timezone.now)
    name = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date', 'meal_type']
        unique_together = ['meal_plan', 'meal_type', 'date']

    def __str__(self):
        return f"{self.get_meal_type_display()} - {self.date}"

    def get_total_calories(self):
        """Calculate total calories for this meal"""
        meal_items = MealItem.objects.filter(meal=self)
        total = 0

        for item in meal_items:
            total += item.food_item.calories * item.servings

        return total

    def get_macros(self):
        """Calculate total macronutrients for this meal"""
        meal_items = MealItem.objects.filter(meal=self)
        protein = 0
        carbs = 0
        fat = 0

        for item in meal_items:
            protein += item.food_item.protein * item.servings
            carbs += item.food_item.carbs * item.servings
            fat += item.food_item.fat * item.servings

        return {
            'protein': protein,
            'carbs': carbs,
            'fat': fat
        }


class MealItem(models.Model):
    """Model representing a food item within a meal"""
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    servings = models.FloatField(default=1.0)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.food_item.name} ({self.servings} servings)"

    def get_calories(self):
        """Calculate calories for this item based on servings"""
        return self.food_item.calories * self.servings

    def get_protein(self):
        """Calculate protein for this item based on servings"""
        return self.food_item.protein * self.servings

    def get_carbs(self):
        """Calculate carbs for this item based on servings"""
        return self.food_item.carbs * self.servings

    def get_fat(self):
        """Calculate fat for this item based on servings"""
        return self.food_item.fat * self.servings


class DailyNutritionLog(models.Model):
    """Model for tracking daily nutrition intake"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nutrition_logs')
    date = models.DateField(default=timezone.now)

    # User-reported values
    calories_consumed = models.PositiveIntegerField(null=True, blank=True)
    protein_consumed = models.FloatField(null=True, blank=True, help_text="Protein in grams")
    carbs_consumed = models.FloatField(null=True, blank=True, help_text="Carbohydrates in grams")
    fat_consumed = models.FloatField(null=True, blank=True, help_text="Fat in grams")
    water_consumed = models.FloatField(null=True, blank=True, help_text="Water in liters")

    # Targets based on active meal plan
    calories_target = models.PositiveIntegerField(null=True, blank=True)
    protein_target = models.FloatField(null=True, blank=True)
    carbs_target = models.FloatField(null=True, blank=True)
    fat_target = models.FloatField(null=True, blank=True)

    notes = models.TextField(blank=True)

    # Was this a cheat day?
    is_cheat_day = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.username} - Nutrition Log - {self.date}"

    def get_calories_percentage(self):
        """Calculate percentage of calories target consumed"""
        if not self.calories_target or self.calories_target == 0:
            return 0
        return (self.calories_consumed / self.calories_target) * 100 if self.calories_consumed else 0

    def get_protein_percentage(self):
        """Calculate percentage of protein target consumed"""
        if not self.protein_target or self.protein_target == 0:
            return 0
        return (self.protein_consumed / self.protein_target) * 100 if self.protein_consumed else 0

    def get_carbs_percentage(self):
        """Calculate percentage of carbs target consumed"""
        if not self.carbs_target or self.carbs_target == 0:
            return 0
        return (self.carbs_consumed / self.carbs_target) * 100 if self.carbs_consumed else 0

    def get_fat_percentage(self):
        """Calculate percentage of fat target consumed"""
        if not self.fat_target or self.fat_target == 0:
            return 0
        return (self.fat_consumed / self.fat_target) * 100 if self.fat_consumed else 0
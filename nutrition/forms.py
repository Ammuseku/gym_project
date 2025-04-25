from django import forms
from .models import FoodItem, MealPlan, Meal, MealItem, DailyNutritionLog
from django.utils import timezone
from django.core.exceptions import ValidationError


class FoodItemForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = [
            'name', 'description', 'serving_size', 'calories',
            'protein', 'carbs', 'fat', 'fiber', 'sugar', 'image_url'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Ensure macros add up properly (each gram of protein and carbs is 4 calories, fat is 9)
        protein_calories = cleaned_data.get('protein', 0) * 4
        carbs_calories = cleaned_data.get('carbs', 0) * 4
        fat_calories = cleaned_data.get('fat', 0) * 9
        total_macro_calories = protein_calories + carbs_calories + fat_calories
        declared_calories = cleaned_data.get('calories', 0)

        # Allow for some rounding error (10% difference)
        calorie_difference = abs(total_macro_calories - declared_calories)
        difference_percentage = (calorie_difference / declared_calories * 100) if declared_calories > 0 else 0

        if difference_percentage > 10:
            raise ValidationError(
                f"The calories ({declared_calories}) do not match the macronutrient values "
                f"(calculated: {int(total_macro_calories)}). Please check your numbers."
            )

        return cleaned_data


class MealPlanForm(forms.ModelForm):
    class Meta:
        model = MealPlan
        fields = [
            'name', 'description', 'goal', 'calories_target',
            'protein_target', 'carbs_target', 'fat_target'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Ensure macros add up properly (each gram of protein and carbs is 4 calories, fat is 9)
        protein_target = cleaned_data.get('protein_target', 0)
        carbs_target = cleaned_data.get('carbs_target', 0)
        fat_target = cleaned_data.get('fat_target', 0)

        protein_calories = protein_target * 4
        carbs_calories = carbs_target * 4
        fat_calories = fat_target * 9
        total_macro_calories = protein_calories + carbs_calories + fat_calories
        calories_target = cleaned_data.get('calories_target', 0)

        # Allow for some rounding error (5% difference)
        calorie_difference = abs(total_macro_calories - calories_target)
        difference_percentage = (calorie_difference / calories_target * 100) if calories_target > 0 else 0

        if difference_percentage > 5:
            raise ValidationError(
                f"The calorie target ({calories_target}) does not match the macronutrient targets "
                f"(calculated: {int(total_macro_calories)}). Please check your numbers."
            )

        return cleaned_data


class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = ['meal_type', 'date', 'name', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.meal_plan = kwargs.pop('meal_plan', None)
        super().__init__(*args, **kwargs)

        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()

    def clean(self):
        cleaned_data = super().clean()
        meal_type = cleaned_data.get('meal_type')
        date = cleaned_data.get('date')

        # Check for duplicate meal types on the same day
        if self.meal_plan and meal_type and date:
            existing_meal = Meal.objects.filter(
                meal_plan=self.meal_plan,
                meal_type=meal_type,
                date=date
            )

            if self.instance.pk:
                existing_meal = existing_meal.exclude(pk=self.instance.pk)

            if existing_meal.exists():
                raise ValidationError(
                    f"You already have a {dict(Meal.MEAL_TYPES)[meal_type]} planned for this day."
                )

        return cleaned_data

    def save(self, commit=True):
        meal = super().save(commit=False)
        if self.meal_plan:
            meal.meal_plan = self.meal_plan

        if commit:
            meal.save()

        return meal


class MealItemForm(forms.ModelForm):
    class Meta:
        model = MealItem
        fields = ['food_item', 'servings', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['food_item'].queryset = FoodItem.objects.all().order_by('name')
        self.fields['servings'].widget.attrs.update({
            'min': '0.25',
            'step': '0.25'
        })


class DailyNutritionLogForm(forms.ModelForm):
    class Meta:
        model = DailyNutritionLog
        fields = [
            'date', 'calories_consumed', 'protein_consumed',
            'carbs_consumed', 'fat_consumed', 'water_consumed',
            'is_cheat_day', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()

            # Try to get targets from active meal plan
            if self.user:
                active_plan = MealPlan.objects.filter(
                    user=self.user,
                    is_active=True
                ).first()

                if active_plan:
                    self.fields['calories_consumed'].help_text = f"Target: {active_plan.calories_target} calories"
                    self.fields['protein_consumed'].help_text = f"Target: {active_plan.protein_target}g"
                    self.fields['carbs_consumed'].help_text = f"Target: {active_plan.carbs_target}g"
                    self.fields['fat_consumed'].help_text = f"Target: {active_plan.fat_target}g"

    def clean_date(self):
        date = self.cleaned_data.get('date')

        # Don't allow logs for future dates
        if date and date > timezone.now().date():
            raise ValidationError("You cannot log nutrition for future dates.")

        # Check for duplicate logs on the same day
        if self.user and date:
            existing_log = DailyNutritionLog.objects.filter(
                user=self.user,
                date=date
            )

            if self.instance.pk:
                existing_log = existing_log.exclude(pk=self.instance.pk)

            if existing_log.exists():
                raise ValidationError("You already have a nutrition log for this date.")

        return date

    def save(self, commit=True):
        log = super().save(commit=False)
        if self.user:
            log.user = self.user

            # Set targets from active meal plan
            active_plan = MealPlan.objects.filter(
                user=self.user,
                is_active=True
            ).first()

            if active_plan:
                log.calories_target = active_plan.calories_target
                log.protein_target = active_plan.protein_target
                log.carbs_target = active_plan.carbs_target
                log.fat_target = active_plan.fat_target

        if commit:
            log.save()

        return log


class FoodSearchForm(forms.Form):
    query = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search for foods...',
            'class': 'form-control'
        })
    )


class NutritionDateRangeForm(forms.Form):
    """Form for filtering nutrition logs by date range"""
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError("End date must be after start date.")

        return cleaned_data


class AIGeneratedMealPlanForm(forms.Form):
    """Form for generating an AI meal plan"""
    GOAL_CHOICES = MealPlan.GOAL_CHOICES

    name = forms.CharField(max_length=100)
    goal = forms.ChoiceField(choices=GOAL_CHOICES)
    calories_per_day = forms.IntegerField(min_value=1200, max_value=4000)
    dietary_restrictions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Enter any dietary restrictions, allergies, or preferences"
    )
    days_to_generate = forms.IntegerField(
        min_value=1,
        max_value=7,
        initial=3,
        help_text="Number of unique days to generate"
    )
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Avg, Sum
from datetime import timedelta
from .models import FoodItem, MealPlan, Meal, MealItem, DailyNutritionLog
from .forms import (
    FoodItemForm, MealPlanForm, MealForm, MealItemForm, DailyNutritionLogForm,
    FoodSearchForm, NutritionDateRangeForm, AIGeneratedMealPlanForm
)
import requests
import json
import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()


@login_required
def nutrition_dashboard(request):
    """Main nutrition dashboard view"""
    # Get active meal plan
    active_plan = MealPlan.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    # Get today's meals if active plan exists
    today = timezone.now().date()
    today_meals = []
    if active_plan:
        today_meals = Meal.objects.filter(
            meal_plan=active_plan,
            date=today
        ).order_by('meal_type')

    # Get recent nutrition logs
    recent_logs = DailyNutritionLog.objects.filter(
        user=request.user
    ).order_by('-date')[:5]

    # Check if today's log exists
    today_log = DailyNutritionLog.objects.filter(
        user=request.user,
        date=today
    ).first()

    context = {
        'active_plan': active_plan,
        'today_meals': today_meals,
        'recent_logs': recent_logs,
        'today_log': today_log,
        'today': today
    }

    return render(request, 'nutrition/dashboard.html', context)


@login_required
def meal_plans(request):
    """View all meal plans"""
    user_plans = MealPlan.objects.filter(
        user=request.user
    ).order_by('-is_active', '-created_at')

    active_plan = None
    for plan in user_plans:
        if plan.is_active:
            active_plan = plan
            break

    context = {
        'plans': user_plans,
        'active_plan': active_plan
    }

    return render(request, 'nutrition/meal_plans.html', context)


@login_required
def create_meal_plan(request):
    """Create a new meal plan"""
    if request.method == 'POST':
        form = MealPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user

            # If this is the first plan, make it active
            if not MealPlan.objects.filter(user=request.user).exists():
                plan.is_active = True

            plan.save()

            messages.success(request, "Meal plan created successfully!")
            return redirect('meal_plan_detail', pk=plan.pk)
    else:
        # Default values based on user profile
        initial = {}
        if hasattr(request.user, 'profile'):
            profile = request.user.profile

            # Calculate TDEE (Total Daily Energy Expenditure) based on profile
            if profile.weight and profile.height and profile.gender and profile.birthdate:
                # Basic BMR calculation using Mifflin-St Jeor formula
                weight_kg = profile.weight
                height_cm = profile.height
                age = profile.age or 25  # Default to 25 if age not available

                if profile.gender == 'M':
                    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
                else:
                    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

                # Activity multiplier
                activity_multiplier = 1.2  # Sedentary
                if profile.fitness_level == 'intermediate':
                    activity_multiplier = 1.5  # Moderate activity
                elif profile.fitness_level == 'advanced':
                    activity_multiplier = 1.7  # Very active

                tdee = int(bmr * activity_multiplier)

                # Adjust based on goal
                if profile.primary_goal == 'fat_loss':
                    calories = tdee - 500  # Deficit
                    goal = 'weight_loss'
                elif profile.primary_goal == 'muscle_gain':
                    calories = tdee + 300  # Surplus
                    goal = 'muscle_gain'
                else:
                    calories = tdee  # Maintenance
                    goal = 'maintenance'

                # Calculate macros (example: 30% protein, 40% carbs, 30% fat)
                protein_pct = 0.3
                carbs_pct = 0.4
                fat_pct = 0.3

                protein_cals = calories * protein_pct
                carbs_cals = calories * carbs_pct
                fat_cals = calories * fat_pct

                protein_g = int(protein_cals / 4)  # 4 calories per gram of protein
                carbs_g = int(carbs_cals / 4)  # 4 calories per gram of carbs
                fat_g = int(fat_cals / 9)  # 9 calories per gram of fat

                initial = {
                    'goal': goal,
                    'calories_target': calories,
                    'protein_target': protein_g,
                    'carbs_target': carbs_g,
                    'fat_target': fat_g,
                    'name': f"{profile.get_primary_goal_display()} Plan"
                }

        form = MealPlanForm(initial=initial)

    context = {
        'form': form,
        'title': 'Create Meal Plan'
    }

    return render(request, 'nutrition/meal_plan_form.html', context)


@login_required
def meal_plan_detail(request, pk):
    """View meal plan details"""
    plan = get_object_or_404(MealPlan, pk=pk, user=request.user)

    # Get meals grouped by date
    meals = Meal.objects.filter(meal_plan=plan).order_by('date', 'meal_type')

    # Group meals by date
    meals_by_date = {}
    for meal in meals:
        if meal.date not in meals_by_date:
            meals_by_date[meal.date] = []
        meals_by_date[meal.date].append(meal)

    context = {
        'plan': plan,
        'meals_by_date': meals_by_date
    }

    return render(request, 'nutrition/meal_plan_detail.html', context)


@login_required
def edit_meal_plan(request, pk):
    """Edit an existing meal plan"""
    plan = get_object_or_404(MealPlan, pk=pk, user=request.user)

    if request.method == 'POST':
        form = MealPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Meal plan updated successfully!")
            return redirect('meal_plan_detail', pk=plan.pk)
    else:
        form = MealPlanForm(instance=plan)

    context = {
        'form': form,
        'plan': plan,
        'title': 'Edit Meal Plan',
        'is_edit': True
    }

    return render(request, 'nutrition/meal_plan_form.html', context)


@login_required
def activate_meal_plan(request, pk):
    """Set a meal plan as active and deactivate others"""
    plan = get_object_or_404(MealPlan, pk=pk, user=request.user)

    # Deactivate all plans for this user
    MealPlan.objects.filter(user=request.user).update(is_active=False)

    # Activate this plan
    plan.is_active = True
    plan.save()

    messages.success(request, f"'{plan.name}' is now your active meal plan.")
    return redirect('meal_plans')


@login_required
def delete_meal_plan(request, pk):
    """Delete a meal plan"""
    plan = get_object_or_404(MealPlan, pk=pk, user=request.user)

    if request.method == 'POST':
        # Check if this is the only active plan
        was_active = plan.is_active

        # Delete the plan
        plan.delete()

        # If this was the active plan, try to activate another one
        if was_active:
            next_plan = MealPlan.objects.filter(user=request.user).order_by('-created_at').first()
            if next_plan:
                next_plan.is_active = True
                next_plan.save()

        messages.success(request, "Meal plan deleted successfully!")
        return redirect('meal_plans')

    context = {
        'plan': plan
    }

    return render(request, 'nutrition/confirm_delete_plan.html', context)


@login_required
def add_meal(request, plan_id):
    """Add a meal to a meal plan"""
    plan = get_object_or_404(MealPlan, pk=plan_id, user=request.user)

    if request.method == 'POST':
        form = MealForm(request.POST, meal_plan=plan)
        if form.is_valid():
            meal = form.save()
            messages.success(request, "Meal added successfully!")
            return redirect('meal_detail', pk=meal.pk)
    else:
        form = MealForm(meal_plan=plan)

    context = {
        'form': form,
        'plan': plan,
        'title': 'Add Meal'
    }

    return render(request, 'nutrition/meal_form.html', context)


@login_required
def meal_detail(request, pk):
    """View meal details and food items"""
    meal = get_object_or_404(Meal, pk=pk, meal_plan__user=request.user)

    # Get food items for this meal
    items = MealItem.objects.filter(meal=meal).select_related('food_item')

    # Calculate meal totals
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0

    for item in items:
        total_calories += item.get_calories()
        total_protein += item.get_protein()
        total_carbs += item.get_carbs()
        total_fat += item.get_fat()

    context = {
        'meal': meal,
        'items': items,
        'totals': {
            'calories': total_calories,
            'protein': total_protein,
            'carbs': total_carbs,
            'fat': total_fat
        }
    }

    return render(request, 'nutrition/meal_detail.html', context)


@login_required
def edit_meal(request, pk):
    """Edit a meal"""
    meal = get_object_or_404(Meal, pk=pk, meal_plan__user=request.user)

    if request.method == 'POST':
        form = MealForm(request.POST, instance=meal, meal_plan=meal.meal_plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Meal updated successfully!")
            return redirect('meal_detail', pk=meal.pk)
    else:
        form = MealForm(instance=meal, meal_plan=meal.meal_plan)

    context = {
        'form': form,
        'meal': meal,
        'title': 'Edit Meal',
        'is_edit': True
    }

    return render(request, 'nutrition/meal_form.html', context)


@login_required
def delete_meal(request, pk):
    """Delete a meal"""
    meal = get_object_or_404(Meal, pk=pk, meal_plan__user=request.user)
    plan_id = meal.meal_plan.id

    if request.method == 'POST':
        meal.delete()
        messages.success(request, "Meal deleted successfully!")
        return redirect('meal_plan_detail', pk=plan_id)

    context = {
        'meal': meal
    }

    return render(request, 'nutrition/confirm_delete_meal.html', context)


@login_required
def add_food_to_meal(request, meal_id):
    """Add a food item to a meal"""
    meal = get_object_or_404(Meal, pk=meal_id, meal_plan__user=request.user)

    if request.method == 'POST':
        form = MealItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.meal = meal
            item.save()

            messages.success(request, "Food item added successfully!")
            return redirect('meal_detail', pk=meal.pk)
    else:
        form = MealItemForm()

    context = {
        'form': form,
        'meal': meal,
        'title': 'Add Food to Meal'
    }

    return render(request, 'nutrition/meal_item_form.html', context)


@login_required
def edit_meal_item(request, pk):
    """Edit a food item in a meal"""
    item = get_object_or_404(MealItem, pk=pk, meal__meal_plan__user=request.user)

    if request.method == 'POST':
        form = MealItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Food item updated successfully!")
            return redirect('meal_detail', pk=item.meal.pk)
    else:
        form = MealItemForm(instance=item)

    context = {
        'form': form,
        'item': item,
        'meal': item.meal,
        'title': 'Edit Food Item',
        'is_edit': True
    }

    return render(request, 'nutrition/meal_item_form.html', context)


@login_required
def delete_meal_item(request, pk):
    """Delete a food item from a meal"""
    item = get_object_or_404(MealItem, pk=pk, meal__meal_plan__user=request.user)
    meal_id = item.meal.id

    if request.method == 'POST':
        item.delete()
        messages.success(request, "Food item removed successfully!")
        return redirect('meal_detail', pk=meal_id)

    context = {
        'item': item,
        'meal': item.meal
    }

    return render(request, 'nutrition/confirm_delete_meal_item.html', context)


@login_required
def food_library(request):
    """View food library and search for foods"""
    query = request.GET.get('query', '')

    if query:
        # Search for foods
        foods = FoodItem.objects.filter(name__icontains=query).order_by('name')
    else:
        # Get all foods, prioritizing user-created ones
        foods = FoodItem.objects.all().order_by('-is_user_created', 'name')[:100]

    # Create search form
    form = FoodSearchForm(initial={'query': query} if query else None)

    context = {
        'foods': foods,
        'form': form,
        'query': query
    }

    return render(request, 'nutrition/food_library.html', context)


@login_required
def add_food(request):
    """Add a new food item to the library"""
    if request.method == 'POST':
        form = FoodItemForm(request.POST)
        if form.is_valid():
            food = form.save(commit=False)
            food.is_user_created = True
            food.created_by = request.user
            food.save()

            messages.success(request, "Food item added successfully!")
            return redirect('food_library')
    else:
        form = FoodItemForm()

    context = {
        'form': form,
        'title': 'Add Food Item'
    }

    return render(request, 'nutrition/food_form.html', context)


@login_required
def food_detail(request, pk):
    """View food item details"""
    food = get_object_or_404(FoodItem, pk=pk)

    context = {
        'food': food
    }

    return render(request, 'nutrition/food_detail.html', context)


@login_required
def edit_food(request, pk):
    """Edit a food item"""
    food = get_object_or_404(FoodItem, pk=pk)

    # Only allow editing if food is user created and created by this user
    if not food.is_user_created or food.created_by != request.user:
        messages.error(request, "You cannot edit this food item.")
        return redirect('food_detail', pk=food.pk)

    if request.method == 'POST':
        form = FoodItemForm(request.POST, instance=food)
        if form.is_valid():
            form.save()
            messages.success(request, "Food item updated successfully!")
            return redirect('food_detail', pk=food.pk)
    else:
        form = FoodItemForm(instance=food)

    context = {
        'form': form,
        'food': food,
        'title': 'Edit Food Item',
        'is_edit': True
    }

    return render(request, 'nutrition/food_form.html', context)


@login_required
def delete_food(request, pk):
    """Delete a food item"""
    food = get_object_or_404(FoodItem, pk=pk)

    # Only allow deletion if food is user created and created by this user
    if not food.is_user_created or food.created_by != request.user:
        messages.error(request, "You cannot delete this food item.")
        return redirect('food_detail', pk=food.pk)

    if request.method == 'POST':
        food.delete()
        messages.success(request, "Food item deleted successfully!")
        return redirect('food_library')

    context = {
        'food': food
    }

    return render(request, 'nutrition/confirm_delete_food.html', context)


@login_required
def log_nutrition(request):
    """Log daily nutrition"""
    if request.method == 'POST':
        form = DailyNutritionLogForm(request.POST, user=request.user)
        if form.is_valid():
            log = form.save()
            messages.success(request, "Nutrition logged successfully!")
            return redirect('nutrition_logs')
    else:
        # Check if log exists for today
        today = timezone.now().date()
        existing_log = DailyNutritionLog.objects.filter(
            user=request.user,
            date=today
        ).first()

        if existing_log:
            # Edit existing log
            form = DailyNutritionLogForm(instance=existing_log, user=request.user)
            is_edit = True
        else:
            # Create new log
            form = DailyNutritionLogForm(user=request.user)
            is_edit = False

    context = {
        'form': form,
        'title': 'Log Nutrition',
        'is_edit': is_edit if 'is_edit' in locals() else False
    }

    return render(request, 'nutrition/log_nutrition.html', context)


@login_required
def nutrition_logs(request):
    """View nutrition logs history"""
    # Create filter form
    form = NutritionDateRangeForm(request.GET)

    # Get all logs
    logs = DailyNutritionLog.objects.filter(user=request.user).order_by('-date')

    # Apply filters if form is valid
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')

        if start_date:
            logs = logs.filter(date__gte=start_date)

        if end_date:
            logs = logs.filter(date__lte=end_date)

    context = {
        'logs': logs,
        'form': form
    }

    return render(request, 'nutrition/nutrition_logs.html', context)


@login_required
def delete_nutrition_log(request, pk):
    """Delete a nutrition log"""
    log = get_object_or_404(DailyNutritionLog, pk=pk, user=request.user)

    if request.method == 'POST':
        log.delete()
        messages.success(request, "Nutrition log deleted successfully!")
        return redirect('nutrition_logs')

    context = {
        'log': log
    }

    return render(request, 'nutrition/confirm_delete_log.html', context)


@login_required
def search_spoonacular(request):
    """Search for foods using Spoonacular API"""
    api_key = os.getenv('SPOONACULAR_API_KEY')

    if not api_key:
        messages.error(request, "Spoonacular API key is not configured.")
        return redirect('food_library')

    query = request.GET.get('query', '')
    results = []

    if query:
        try:
            # Make API request to Spoonacular
            url = f"https://api.spoonacular.com/food/ingredients/search"
            params = {
                'apiKey': api_key,
                'query': query,
                'number': 10,
                'metaInformation': True
            }

            response = requests.get(url, params=params)
            data = response.json()

            if 'results' in data:
                results = data['results']
        except Exception as e:
            messages.error(request, f"Error searching foods: {str(e)}")

    context = {
        'query': query,
        'results': results
    }

    return render(request, 'nutrition/search_results.html', context)


@login_required
def add_spoonacular_food(request, spoonacular_id):
    """Add a food from Spoonacular API to the food library"""
    api_key = os.getenv('SPOONACULAR_API_KEY')

    if not api_key:
        messages.error(request, "Spoonacular API key is not configured.")
        return redirect('food_library')

    try:
        # Check if food already exists
        existing_food = FoodItem.objects.filter(external_id=str(spoonacular_id)).first()
        if existing_food:
            messages.info(request, f"'{existing_food.name}' is already in your food library.")
            return redirect('food_detail', pk=existing_food.pk)

        # Get food details from Spoonacular
        url = f"https://api.spoonacular.com/food/ingredients/{spoonacular_id}/information"
        params = {
            'apiKey': api_key,
            'amount': 100,
            'unit': 'grams'
        }

        response = requests.get(url, params=params)
        data = response.json()

        if 'name' in data:
            # Extract nutrition data
            nutrients = {}
            for nutrient in data.get('nutrition', {}).get('nutrients', []):
                nutrients[nutrient['name'].lower()] = nutrient['amount']

            # Create new food item
            food = FoodItem(
                name=data['name'].title(),
                description=f"Imported from Spoonacular - {data.get('original', '')}",
                serving_size="100g",
                calories=int(nutrients.get('calories', 0)),
                protein=round(nutrients.get('protein', 0), 1),
                carbs=round(nutrients.get('carbohydrates', 0), 1),
                fat=round(nutrients.get('fat', 0), 1),
                fiber=round(nutrients.get('fiber', 0), 1),
                sugar=round(nutrients.get('sugar', 0), 1),
                external_id=str(spoonacular_id),
                image_url=f"https://spoonacular.com/cdn/ingredients_100x100/{data.get('image', '')}",
                is_user_created=False
            )

            food.save()

            messages.success(request, f"'{food.name}' added to your food library.")
            return redirect('food_detail', pk=food.pk)
        else:
            messages.error(request, "Could not retrieve food information.")

    except Exception as e:
        messages.error(request, f"Error adding food: {str(e)}")

    return redirect('food_library')


@login_required
def generate_ai_meal_plan(request):
    """Generate a meal plan using OpenAI (improved version)"""
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if not openai_api_key:
        messages.error(request, "OpenAI API key is not configured.")
        return redirect('meal_plans')

    if request.method == 'POST':
        form = AIGeneratedMealPlanForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            goal = form.cleaned_data.get('goal')
            calories = form.cleaned_data.get('calories_per_day')
            restrictions = form.cleaned_data.get('dietary_restrictions', '')
            days = form.cleaned_data.get('days_to_generate')

            try:
                # Calculate macros based on goal
                if goal == 'weight_loss':
                    protein_pct = 0.35  # Higher protein for weight loss
                    carbs_pct = 0.35
                    fat_pct = 0.30
                elif goal == 'muscle_gain':
                    protein_pct = 0.30
                    carbs_pct = 0.45  # Higher carbs for muscle gain
                    fat_pct = 0.25
                else:  # maintenance
                    protein_pct = 0.30
                    carbs_pct = 0.40
                    fat_pct = 0.30

                protein_cals = calories * protein_pct
                carbs_cals = calories * carbs_pct
                fat_cals = calories * fat_pct

                protein_g = int(protein_cals / 4)
                carbs_g = int(carbs_cals / 4)
                fat_g = int(fat_cals / 9)

                # Create meal plan in database
                plan = MealPlan.objects.create(
                    user=request.user,
                    name=name,
                    description=f"AI-generated meal plan for {goal.replace('_', ' ')}",
                    goal=goal,
                    calories_target=calories,
                    protein_target=protein_g,
                    carbs_target=carbs_g,
                    fat_target=fat_g,
                    is_ai_generated=True
                )

                # Проверяем наличие продуктов в базе данных
                available_foods = FoodItem.objects.all()
                if available_foods.count() < 5:
                    messages.error(request,
                                   "Not enough food items in database. Please add more items to the food library.")
                    return redirect('food_library')

                # Создаем план из имеющихся продуктов вместо вызова OpenAI
                create_meal_plan_from_available_foods(plan, days, goal, calories, protein_g, carbs_g, fat_g,
                                                      restrictions)

                messages.success(request, "AI meal plan generated successfully!")
                return redirect('meal_plan_detail', pk=plan.pk)

            except Exception as e:
                messages.error(request, f"Error generating meal plan: {str(e)}")
                return redirect('meal_plans')
    else:
        form = AIGeneratedMealPlanForm()

    context = {
        'form': form,
        'title': 'Generate AI Meal Plan'
    }

    return render(request, 'nutrition/generate_ai_meal_plan.html', context)


@login_required
def generate_ai_meal_plan(request):
    """Generate a meal plan with automatic meal creation"""
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if request.method == 'POST':
        form = AIGeneratedMealPlanForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            goal = form.cleaned_data.get('goal')
            calories = form.cleaned_data.get('calories_per_day')
            restrictions = form.cleaned_data.get('dietary_restrictions', '')
            days = form.cleaned_data.get('days_to_generate')

            try:
                # Calculate macros based on goal
                if goal == 'weight_loss':
                    protein_pct = 0.35  # Higher protein for weight loss
                    carbs_pct = 0.35
                    fat_pct = 0.30
                elif goal == 'muscle_gain':
                    protein_pct = 0.30
                    carbs_pct = 0.45  # Higher carbs for muscle gain
                    fat_pct = 0.25
                else:  # maintenance
                    protein_pct = 0.30
                    carbs_pct = 0.40
                    fat_pct = 0.30

                protein_cals = calories * protein_pct
                carbs_cals = calories * carbs_pct
                fat_cals = calories * fat_pct

                protein_g = int(protein_cals / 4)
                carbs_g = int(carbs_cals / 4)
                fat_g = int(fat_cals / 9)

                # Create meal plan in database
                plan = MealPlan.objects.create(
                    user=request.user,
                    name=name,
                    description=f"AI-generated meal plan for {goal.replace('_', ' ')}",
                    goal=goal,
                    calories_target=calories,
                    protein_target=protein_g,
                    carbs_target=carbs_g,
                    fat_target=fat_g,
                    is_ai_generated=True
                )

                # Проверяем наличие продуктов в базе данных
                food_count = FoodItem.objects.count()

                if food_count < 5:
                    messages.warning(request, f"Only {food_count} food items found. Your meal plan might be limited.")

                # Создаем базовый план питания с автоматическим добавлением блюд
                add_meals_to_plan(plan, days)

                messages.success(request, "AI meal plan generated successfully!")
                return redirect('meal_plan_detail', pk=plan.pk)

            except Exception as e:
                messages.error(request, f"Error generating meal plan: {str(e)}")
                return redirect('meal_plans')
    else:
        form = AIGeneratedMealPlanForm()

    context = {
        'form': form,
        'title': 'Generate AI Meal Plan'
    }

    return render(request, 'nutrition/generate_ai_meal_plan.html', context)


def add_meals_to_plan(plan, days=7):
    """
    Добавляет стандартные приемы пищи в план на указанное количество дней
    """
    today = timezone.now().date()

    # Получаем все доступные продукты
    available_foods = FoodItem.objects.all()
    if not available_foods.exists():
        # Если продуктов нет, возвращаемся
        return

    # Стандартные типы приемов пищи
    meal_types = ['breakfast', 'lunch', 'dinner', 'snack']

    # Если цель - набор массы, добавляем предтренировочный прием пищи
    if plan.goal == 'muscle_gain':
        meal_types.append('pre_workout')

    # Создаем приемы пищи на каждый день
    for day_num in range(days):
        day_date = today + timezone.timedelta(days=day_num)

        for meal_type in meal_types:
            # Создаем прием пищи
            meal = Meal.objects.create(
                meal_plan=plan,
                meal_type=meal_type,
                date=day_date,
                name=f"Day {day_num + 1} - {meal_type.capitalize()}"
            )

            # Добавляем в каждый прием пищи 2-3 случайных продукта
            for _ in range(min(3, available_foods.count())):
                # Выбираем случайный продукт
                random_food = available_foods.order_by('?').first()

                # Устанавливаем случайное количество порций (от 0.5 до 2.0)
                # Округляем до 0.5 для реалистичности
                import random
                servings = round(random.uniform(0.5, 2.0) * 2) / 2

                # Создаем элемент приема пищи
                MealItem.objects.create(
                    meal=meal,
                    food_item=random_food,
                    servings=servings,
                    notes=f"{servings} serving(s)"
                )

def ensure_basic_dishes_exist():
    """Проверяет и добавляет базовые блюда в базу данных, если их нет"""
    # Создаем или получаем системного пользователя
    system_user, created = User.objects.get_or_create(username='system', defaults={'is_staff': True})

    # Базовые блюда
    basic_dishes = [
        {
            "name": "Brown Rice",
            "description": "Cooked brown rice",
            "serving_size": "1 cup (200g)",
            "calories": 216,
            "protein": 5.0,
            "carbs": 45.0,
            "fat": 1.8,
            "fiber": 3.5,
            "sugar": 0.7,
            "is_user_created": False,
            "created_by": system_user
        },
        {
            "name": "Mashed Potatoes",
            "description": "Homemade mashed potatoes",
            "serving_size": "1 cup (240g)",
            "calories": 237,
            "protein": 5.0,
            "carbs": 35.0,
            "fat": 9.0,
            "fiber": 4.0,
            "sugar": 3.0,
            "is_user_created": False,
            "created_by": system_user
        },
        {
            "name": "Pasta with Sauce",
            "description": "Whole wheat pasta with tomato sauce",
            "serving_size": "1 cup (250g)",
            "calories": 280,
            "protein": 10.0,
            "carbs": 54.0,
            "fat": 3.5,
            "fiber": 6.0,
            "sugar": 8.0,
            "is_user_created": False,
            "created_by": system_user
        },
        {
            "name": "Chicken Breast (cooked)",
            "description": "Grilled chicken breast",
            "serving_size": "100g",
            "calories": 165,
            "protein": 31.0,
            "carbs": 0.0,
            "fat": 3.6,
            "fiber": 0.0,
            "sugar": 0.0,
            "is_user_created": False,
            "created_by": system_user
        },
        {
            "name": "Scrambled Eggs",
            "description": "Scrambled eggs with salt and pepper",
            "serving_size": "2 eggs",
            "calories": 180,
            "protein": 12.0,
            "carbs": 2.0,
            "fat": 14.0,
            "fiber": 0.0,
            "sugar": 0.0,
            "is_user_created": False,
            "created_by": system_user
        },
        {
            "name": "Greek Salad",
            "description": "Mixed greens with feta cheese and olive oil",
            "serving_size": "1 bowl (200g)",
            "calories": 150,
            "protein": 5.0,
            "carbs": 10.0,
            "fat": 10.0,
            "fiber": 3.0,
            "sugar": 5.0,
            "is_user_created": False,
            "created_by": system_user
        },
        {
            "name": "Fruit Smoothie",
            "description": "Mixed berries and banana smoothie",
            "serving_size": "1 cup (250ml)",
            "calories": 150,
            "protein": 2.0,
            "carbs": 32.0,
            "fat": 1.0,
            "fiber": 4.0,
            "sugar": 25.0,
            "is_user_created": False,
            "created_by": system_user
        },
        {
            "name": "Avocado Toast",
            "description": "Whole grain toast with avocado",
            "serving_size": "1 slice",
            "calories": 200,
            "protein": 5.0,
            "carbs": 20.0,
            "fat": 10.0,
            "fiber": 5.0,
            "sugar": 2.0,
            "is_user_created": False,
            "created_by": system_user
        }
    ]

    # Проверяем и добавляем базовые блюда, если их нет
    for dish in basic_dishes:
        if not FoodItem.objects.filter(name=dish["name"]).exists():
            FoodItem.objects.create(**dish)


def create_meal_plan_from_available_foods(plan, days, goal, calories_target, protein_target, carbs_target, fat_target,
                                          restrictions=None):
    """
    Создает план питания из доступных продуктов с отладочной информацией
    и гарантированным созданием приемов пищи
    """
    today = timezone.now().date()
    created_meals = False  # Флаг успешного создания

    try:
        # Получаем доступные продукты
        available_foods = FoodItem.objects.all()

        if available_foods.count() < 5:
            # Если продуктов меньше 5, просто возвращаем False
            return False

        # Применяем фильтрацию по диетическим ограничениям, если они указаны
        if restrictions:
            restrictions_lower = restrictions.lower()

            # Исключаем мясные продукты для вегетарианцев
            if 'vegetarian' in restrictions_lower or 'vegan' in restrictions_lower:
                available_foods = available_foods.exclude(
                    description__icontains='meat'
                ).exclude(
                    description__icontains='chicken'
                ).exclude(
                    description__icontains='beef'
                ).exclude(
                    description__icontains='pork'
                ).exclude(
                    description__icontains='turkey'
                )

            # Исключаем все животные продукты для веганов
            if 'vegan' in restrictions_lower:
                available_foods = available_foods.exclude(
                    description__icontains='dairy'
                ).exclude(
                    description__icontains='milk'
                ).exclude(
                    description__icontains='cheese'
                ).exclude(
                    description__icontains='yogurt'
                ).exclude(
                    description__icontains='egg'
                )

            # Исключаем продукты с глютеном
            if 'gluten' in restrictions_lower or 'gluten-free' in restrictions_lower:
                available_foods = available_foods.exclude(
                    description__icontains='wheat'
                ).exclude(
                    description__icontains='bread'
                ).exclude(
                    description__icontains='pasta'
                ).exclude(
                    description__icontains='barley'
                ).exclude(
                    description__icontains='rye'
                )

            # Исключаем продукты с лактозой
            if 'lactose' in restrictions_lower or 'dairy-free' in restrictions_lower:
                available_foods = available_foods.exclude(
                    description__icontains='milk'
                ).exclude(
                    description__icontains='cheese'
                ).exclude(
                    description__icontains='yogurt'
                ).exclude(
                    description__icontains='dairy'
                )

        # Определяем стандартные типы приемов пищи
        standard_meals = [
            {
                'type': 'breakfast',
                'name': 'Breakfast',
                'percent': 0.25,  # 25% дневных калорий
            },
            {
                'type': 'lunch',
                'name': 'Lunch',
                'percent': 0.35,  # 35% дневных калорий
            },
            {
                'type': 'dinner',
                'name': 'Dinner',
                'percent': 0.30,  # 30% дневных калорий
            },
            {
                'type': 'snack',
                'name': 'Snack',
                'percent': 0.10,  # 10% дневных калорий
            }
        ]

        # Для набора массы добавляем предтренировочный прием пищи
        if goal == 'muscle_gain':
            standard_meals.append({
                'type': 'pre_workout',
                'name': 'Pre-Workout Snack',
                'percent': 0.10,  # 10% дневных калорий
            })
            # Корректируем другие приемы пищи
            standard_meals[0]['percent'] = 0.20  # Breakfast: 20%
            standard_meals[1]['percent'] = 0.30  # Lunch: 30%
            standard_meals[2]['percent'] = 0.30  # Dinner: 30%
            standard_meals[3]['percent'] = 0.10  # Snack: 10%

        # Создаем план на указанное количество дней
        for day_num in range(days):
            day_date = today + timezone.timedelta(days=day_num)

            # Для каждого дня создаем стандартные приемы пищи
            for meal_info in standard_meals:
                # Если это предтренировочный прием пищи для не набора массы, пропускаем
                if meal_info['type'] == 'pre_workout' and goal != 'muscle_gain':
                    continue

                # Создаем прием пищи
                meal = Meal.objects.create(
                    meal_plan=plan,
                    meal_type=meal_info['type'],
                    date=day_date,
                    name=f"Day {day_num + 1} - {meal_info['name']}"
                )

                # Расчет целевых калорий для этого приема пищи
                meal_calories = int(calories_target * meal_info['percent'])

                # Добавляем минимум 2-3 продукта в каждый прием пищи
                for _ in range(min(3, available_foods.count())):
                    # Выбираем случайный продукт
                    random_food = available_foods.order_by('?').first()
                    if random_food:
                        # Рассчитываем количество порций для достижения примерных калорий
                        if random_food.calories <= 0:
                            servings = 1.0  # Стандартная порция если калорий нет
                        else:
                            # Пытаемся распределить калории равномерно
                            servings = round((meal_calories / 3) / random_food.calories, 1)
                            servings = max(min(servings, 2.0), 0.5)  # Ограничиваем от 0.5 до 2 порций

                        # Создаем элемент приема пищи
                        MealItem.objects.create(
                            meal=meal,
                            food_item=random_food,
                            servings=servings,
                            notes=f"{servings:.1f} serving(s)"
                        )

                        # Исключаем этот продукт из дальнейшего выбора для этого приема пищи
                        available_foods = available_foods.exclude(id=random_food.id)

                created_meals = True  # Помечаем, что создали хотя бы один прием пищи

        return created_meals

    except Exception as e:
        # Логируем ошибку, но не прерываем выполнение
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating meal plan: {str(e)}")
        return created_meals
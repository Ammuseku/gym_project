from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from datetime import timedelta, date
from .models import (
    MuscleGroup, Exercise, WorkoutPlan, PlanExercise,
    UserWorkoutPlan, UserPlanExercise, WorkoutSchedule
)
from .forms import (
    MuscleGroupForm, ExerciseForm, WorkoutPlanForm, PlanExerciseForm,
    PlanExerciseFormSet, UserPlanExerciseForm, WorkoutScheduleForm,
    ExerciseFilterForm, WorkoutPlanFilterForm
)
from progress.models import WorkoutLog


@login_required
def dashboard(request):
    # Get user's active workout plans
    active_plans = UserWorkoutPlan.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('workout_plan')

    # Get upcoming scheduled workouts
    today = timezone.now().date()
    upcoming_workouts = WorkoutSchedule.objects.filter(
        user=request.user,
        date__gte=today,
        completed=False
    ).order_by('date', 'start_time')[:5]

    # Get recent workout logs
    recent_logs = WorkoutLog.objects.filter(
        user=request.user
    ).order_by('-date')[:5]

    # Get workout suggestions based on user profile
    suggested_plans = []
    if hasattr(request.user, 'profile'):
        profile = request.user.profile
        suggested_plans = WorkoutPlan.objects.filter(
            is_public=True,
            goal=profile.primary_goal
        ).exclude(
            users__user=request.user
        ).order_by('-created_at')[:3]

    context = {
        'active_plans': active_plans,
        'upcoming_workouts': upcoming_workouts,
        'recent_logs': recent_logs,
        'suggested_plans': suggested_plans,
    }

    return render(request, 'workouts/dashboard.html', context)


@login_required
def exercise_library(request):
    form = ExerciseFilterForm(request.GET)
    exercises = Exercise.objects.all()

    # Apply filters
    if form.is_valid():
        if form.cleaned_data['search']:
            query = form.cleaned_data['search']
            exercises = exercises.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )

        if form.cleaned_data['muscle_group']:
            muscle_group = form.cleaned_data['muscle_group']
            exercises = exercises.filter(
                Q(muscle_group=muscle_group) |
                Q(secondary_muscle_groups=muscle_group)
            ).distinct()

        if form.cleaned_data['difficulty']:
            exercises = exercises.filter(difficulty=form.cleaned_data['difficulty'])

        if form.cleaned_data['category']:
            exercises = exercises.filter(category=form.cleaned_data['category'])

        if form.cleaned_data['equipment']:
            equipment = form.cleaned_data['equipment']
            exercises = exercises.filter(equipment_needed__icontains=equipment)

    # Get all muscle groups for sidebar
    muscle_groups = MuscleGroup.objects.annotate(
        exercise_count=Count('exercises')
    ).order_by('name')

    context = {
        'exercises': exercises,
        'muscle_groups': muscle_groups,
        'form': form,
    }

    return render(request, 'workouts/exercise_library.html', context)


@login_required
def exercise_detail(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)

    # Get user's exercise logs for this exercise
    logs = UserPlanExercise.objects.filter(
        user=request.user,
        plan_exercise__exercise=exercise
    ).order_by('-date')[:10]

    # Get similar exercises
    similar_exercises = Exercise.objects.filter(
        muscle_group=exercise.muscle_group
    ).exclude(pk=exercise.pk)[:4]

    context = {
        'exercise': exercise,
        'logs': logs,
        'similar_exercises': similar_exercises
    }

    return render(request, 'workouts/exercise_detail.html', context)


@login_required
def workout_plans(request):
    form = WorkoutPlanFilterForm(request.GET)

    # Get plans created by user or public plans
    plans = WorkoutPlan.objects.filter(
        Q(created_by=request.user) | Q(is_public=True)
    ).distinct()

    # Apply filters
    if form.is_valid():
        if form.cleaned_data['search']:
            query = form.cleaned_data['search']
            plans = plans.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )

        if form.cleaned_data['goal']:
            plans = plans.filter(goal=form.cleaned_data['goal'])

        if form.cleaned_data['intensity']:
            plans = plans.filter(intensity=form.cleaned_data['intensity'])

        if form.cleaned_data['duration']:
            plans = plans.filter(duration_weeks__lte=form.cleaned_data['duration'])

    # Get user's active plans
    active_plan_ids = UserWorkoutPlan.objects.filter(
        user=request.user,
        is_active=True
    ).values_list('workout_plan_id', flat=True)

    context = {
        'plans': plans,
        'form': form,
        'active_plan_ids': active_plan_ids
    }

    return render(request, 'workouts/workout_plans.html', context)


@login_required
def plan_detail(request, pk):
    plan = get_object_or_404(WorkoutPlan, pk=pk)

    # Check if user is allowed to view this plan
    if not plan.is_public and plan.created_by != request.user:
        messages.error(request, "You don't have permission to view this workout plan.")
        return redirect('workout_plans')

    # Check if user is following this plan
    is_following = UserWorkoutPlan.objects.filter(
        user=request.user,
        workout_plan=plan,
        is_active=True
    ).exists()

    # Get exercises by day of week
    weekly_workouts = plan.get_weekly_workouts()

    context = {
        'plan': plan,
        'weekly_workouts': weekly_workouts,
        'is_following': is_following
    }

    return render(request, 'workouts/plan_detail.html', context)


@login_required
def create_plan(request):
    if request.method == 'POST':
        form = WorkoutPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.created_by = request.user
            plan.save()

            messages.success(request, "Workout plan created successfully! Now add exercises to your plan.")
            return redirect('edit_plan', pk=plan.pk)
    else:
        form = WorkoutPlanForm()

    context = {
        'form': form,
        'title': 'Create Workout Plan'
    }

    return render(request, 'workouts/plan_form.html', context)


@login_required
def edit_plan(request, pk):
    plan = get_object_or_404(WorkoutPlan, pk=pk)

    # Check if user is allowed to edit this plan
    if plan.created_by != request.user:
        messages.error(request, "You don't have permission to edit this workout plan.")
        return redirect('workout_plans')

    if request.method == 'POST':
        form = WorkoutPlanForm(request.POST, instance=plan)
        formset = PlanExerciseFormSet(request.POST, instance=plan)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            messages.success(request, "Workout plan updated successfully!")
            return redirect('plan_detail', pk=plan.pk)
    else:
        form = WorkoutPlanForm(instance=plan)
        formset = PlanExerciseFormSet(instance=plan)

    context = {
        'form': form,
        'formset': formset,
        'plan': plan,
        'title': 'Edit Workout Plan'
    }

    return render(request, 'workouts/plan_edit.html', context)


@login_required
def delete_plan(request, pk):
    plan = get_object_or_404(WorkoutPlan, pk=pk)

    # Check if user is allowed to delete this plan
    if plan.created_by != request.user:
        messages.error(request, "You don't have permission to delete this workout plan.")
        return redirect('workout_plans')

    if request.method == 'POST':
        plan.delete()
        messages.success(request, "Workout plan deleted successfully!")
        return redirect('workout_plans')

    context = {
        'plan': plan
    }

    return render(request, 'workouts/plan_confirm_delete.html', context)


@login_required
def follow_plan(request, pk):
    plan = get_object_or_404(WorkoutPlan, pk=pk)

    # Check if user is already following this plan
    existing_plan = UserWorkoutPlan.objects.filter(
        user=request.user,
        workout_plan=plan,
        is_active=True
    ).first()

    if existing_plan:
        messages.info(request, "You are already following this workout plan.")
        return redirect('plan_detail', pk=plan.pk)

    # Create new user workout plan
    UserWorkoutPlan.objects.create(
        user=request.user,
        workout_plan=plan,
        start_date=timezone.now().date()
    )

    messages.success(request, f"You are now following the '{plan.name}' workout plan!")
    return redirect('plan_detail', pk=plan.pk)


@login_required
def unfollow_plan(request, pk):
    plan = get_object_or_404(WorkoutPlan, pk=pk)

    # Get user's active plan
    user_plan = UserWorkoutPlan.objects.filter(
        user=request.user,
        workout_plan=plan,
        is_active=True
    ).first()

    if not user_plan:
        messages.info(request, "You are not following this workout plan.")
        return redirect('plan_detail', pk=plan.pk)

    if request.method == 'POST':
        # Deactivate the plan instead of deleting
        user_plan.is_active = False
        user_plan.end_date = timezone.now().date()
        user_plan.save()

        messages.success(request, f"You have unfollowed the '{plan.name}' workout plan.")
        return redirect('workout_plans')

    context = {
        'plan': plan
    }

    return render(request, 'workouts/plan_confirm_unfollow.html', context)


@login_required
def schedule_workout(request):
    if request.method == 'POST':
        form = WorkoutScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = request.user
            schedule.save()

            messages.success(request, "Workout scheduled successfully!")
            return redirect('schedule')
    else:
        form = WorkoutScheduleForm(user=request.user)

    context = {
        'form': form,
        'title': 'Schedule Workout'
    }

    return render(request, 'workouts/schedule_form.html', context)


@login_required
def schedule(request):
    today = timezone.now().date()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)

    # Get next 7 days for weekly view
    week_dates = [start_date + timedelta(days=i) for i in range(7)]

    # Get schedules for this week
    schedules = WorkoutSchedule.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).order_by('date', 'start_time')

    # Organize schedules by day
    schedule_by_day = {day: [] for day in week_dates}
    for schedule in schedules:
        schedule_by_day[schedule.date].append(schedule)

    # Get active plans for sidebar
    active_plans = UserWorkoutPlan.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('workout_plan')

    context = {
        'week_dates': week_dates,
        'schedule_by_day': schedule_by_day,
        'active_plans': active_plans,
        'today': today
    }

    return render(request, 'workouts/schedule.html', context)


@login_required
def log_workout(request, schedule_id):
    schedule = get_object_or_404(WorkoutSchedule, pk=schedule_id, user=request.user)
    exercises = schedule.get_exercises()

    if request.method == 'POST':
        all_valid = True
        forms = []

        # Process each exercise form
        for exercise in exercises:
            prefix = f"exercise_{exercise.id}"
            form = UserPlanExerciseForm(
                request.POST,
                prefix=prefix,
                instance=UserPlanExercise(
                    user=request.user,
                    plan_exercise=exercise,
                    date=schedule.date
                )
            )

            if form.is_valid():
                forms.append(form)
            else:
                all_valid = False

        if all_valid:
            # Save all forms
            for form in forms:
                form.save()

            # Mark schedule as completed
            schedule.mark_as_completed()

            # Create workout log
            WorkoutLog.objects.create(
                user=request.user,
                date=schedule.date,
                duration=None,
                notes=""
            )

            messages.success(request, "Workout logged successfully!")
            return redirect('schedule')
    else:
        # Initialize forms for each exercise
        for exercise in exercises:
            # Check if there's already a log
            existing_log = UserPlanExercise.objects.filter(
                user=request.user,
                plan_exercise=exercise,
                date=schedule.date
            ).first()

            if existing_log:
                exercise.form = UserPlanExerciseForm(
                    instance=existing_log,
                    prefix=f"exercise_{exercise.id}"
                )
            else:
                # Try to get previous logs for weight suggestion
                previous_log = UserPlanExercise.objects.filter(
                    user=request.user,
                    plan_exercise__exercise=exercise.exercise
                ).order_by('-date').first()

                initial_data = {}
                if previous_log:
                    initial_data['weight'] = previous_log.weight

                exercise.form = UserPlanExerciseForm(
                    initial=initial_data,
                    prefix=f"exercise_{exercise.id}"
                )

    context = {
        'schedule': schedule,
        'exercises': exercises
    }

    return render(request, 'workouts/log_workout.html', context)


@login_required
def mark_workout_completed(request, schedule_id):
    schedule = get_object_or_404(WorkoutSchedule, pk=schedule_id, user=request.user)

    if request.method == 'POST':
        schedule.mark_as_completed()

        # Create workout log
        WorkoutLog.objects.create(
            user=request.user,
            date=schedule.date,
            duration=None,
            notes="Marked as completed (no details logged)"
        )

        messages.success(request, "Workout marked as completed!")

        # Redirect back to referring page
        next_page = request.POST.get('next', 'schedule')
        return redirect(next_page)

    return redirect('schedule')


@login_required
# Функция для обновления в views.py

@login_required
def generate_ai_plan(request):
    """Generate a workout plan using AI (improved version with realistic exercise count)"""
    # Получаем все возможные цели из модели WorkoutPlan
    goals = [choice[0] for choice in WorkoutPlan.GOAL_CHOICES]
    fitness_levels = [choice[0] for choice in Exercise.DIFFICULTY_CHOICES]

    if request.method == 'POST':
        goal = request.POST.get('goal')
        fitness_level = request.POST.get('fitness_level')
        days_per_week = int(request.POST.get('days_per_week', 3))
        preferences = request.POST.get('preferences', '')

        # Создаем план тренировок
        plan = WorkoutPlan(
            name=f"{fitness_level.capitalize()} {goal.replace('_', ' ').title()} Plan",
            description=f"Custom {days_per_week}-day {fitness_level} workout plan for {goal.replace('_', ' ')}." +
                        (f" Note: {preferences}" if preferences else ""),
            goal=goal,
            intensity='medium' if fitness_level == 'intermediate' else (
                'low' if fitness_level == 'beginner' else 'high'),
            duration_weeks=8,
            created_by=request.user,
            is_public=False
        )
        plan.save()

        # Получаем все группы мышц
        all_muscle_groups = MuscleGroup.objects.all()

        # Структура плана в зависимости от цели и количества упражнений
        plan_structure = {}

        # Определяем количество упражнений в зависимости от уровня тренированности
        if fitness_level == 'beginner':
            exercises_per_workout = 3  # Для новичков меньше упражнений
        elif fitness_level == 'intermediate':
            exercises_per_workout = 4  # Для среднего уровня чуть больше
        else:
            exercises_per_workout = 5  # Для продвинутых больше упражнений

        # Дополнительно настраиваем количество упражнений, если в предпочтениях указаны определенные условия
        if 'короткие тренировки' in preferences.lower() or 'быстрые тренировки' in preferences.lower():
            exercises_per_workout = min(exercises_per_workout, 3)  # Уменьшаем для коротких тренировок
        elif 'длинные тренировки' in preferences.lower() or 'больше упражнений' in preferences.lower():
            exercises_per_workout = min(exercises_per_workout + 1, 5)  # Увеличиваем, но не более 5

        # Создаем структуру плана в зависимости от цели
        if goal == 'muscle_gain':
            if days_per_week <= 3:
                # Full body workouts for fewer days
                for day in range(days_per_week):
                    # Для тренировки всего тела выбираем группы мышц равномерно
                    selected_muscle_groups = select_diverse_muscle_groups(all_muscle_groups, exercises_per_workout)
                    plan_structure[day] = {
                        'name': f"Full Body Workout {day + 1}",
                        'muscles': selected_muscle_groups,
                        'exercises_per_muscle': 1  # По 1 упражнению на группу мышц
                    }
            elif days_per_week == 4:
                # Upper/Lower split
                upper_muscles = MuscleGroup.objects.filter(name__in=["Chest", "Back", "Shoulders", "Arms"])
                lower_muscles = MuscleGroup.objects.filter(name__in=["Legs", "Glutes"])
                core = MuscleGroup.objects.filter(name="Core")

                # Для верхней части равномерно выбираем группы мышц
                upper_day1 = select_diverse_muscle_groups(upper_muscles, exercises_per_workout - 1)
                upper_day2 = select_diverse_muscle_groups(upper_muscles, exercises_per_workout - 1, exclude=upper_day1)

                # Добавляем кор к обоим дням верхней части
                plan_structure[0] = {'name': "Upper Body A", 'muscles': list(upper_day1) + list(core),
                                     'exercises_per_muscle': 1}
                plan_structure[2] = {'name': "Upper Body B", 'muscles': list(upper_day2) + list(core),
                                     'exercises_per_muscle': 1}

                # Для нижней части выбираем больше упражнений, чтобы тренировка была не слишком короткой
                plan_structure[1] = {'name': "Lower Body A", 'muscles': list(lower_muscles), 'exercises_per_muscle': 2}
                plan_structure[3] = {'name': "Lower Body B", 'muscles': list(lower_muscles), 'exercises_per_muscle': 2}
            else:
                # Push/Pull/Legs split for 5-6 days
                push_muscles = MuscleGroup.objects.filter(name__in=["Chest", "Shoulders"])
                pull_muscles = MuscleGroup.objects.filter(name__in=["Back"])
                leg_muscles = MuscleGroup.objects.filter(name__in=["Legs", "Glutes"])
                arms = MuscleGroup.objects.filter(name="Arms")
                core = MuscleGroup.objects.filter(name="Core")

                # День 1: Push - грудь, плечи, трицепс
                plan_structure[0] = {
                    'name': "Push Day (Chest, Shoulders, Triceps)",
                    'muscles': list(select_diverse_muscle_groups(push_muscles, exercises_per_workout - 1)) + list(arms),
                    'exercises_per_muscle': 1
                }

                # День 2: Pull - спина, бицепс
                plan_structure[1] = {
                    'name': "Pull Day (Back, Biceps)",
                    'muscles': list(select_diverse_muscle_groups(pull_muscles, exercises_per_workout - 1)) + list(arms),
                    'exercises_per_muscle': 1
                }

                # День 3: Legs - ноги, ягодицы, кор
                plan_structure[2] = {
                    'name': "Leg Day",
                    'muscles': list(select_diverse_muscle_groups(leg_muscles, exercises_per_workout - 1)) + list(core),
                    'exercises_per_muscle': 1
                }

                # Для 5-6 дней добавляем вторую итерацию сплита
                if days_per_week >= 5:
                    plan_structure[3] = {
                        'name': "Push Day B",
                        'muscles': list(select_diverse_muscle_groups(push_muscles, exercises_per_workout - 1,
                                                                     exclude=plan_structure[0]['muscles'])) + list(
                            arms),
                        'exercises_per_muscle': 1
                    }
                    plan_structure[4] = {
                        'name': "Pull Day B",
                        'muscles': list(select_diverse_muscle_groups(pull_muscles, exercises_per_workout - 1,
                                                                     exclude=plan_structure[1]['muscles'])) + list(
                            arms),
                        'exercises_per_muscle': 1
                    }

                if days_per_week == 6:
                    plan_structure[5] = {
                        'name': "Leg Day B",
                        'muscles': list(select_diverse_muscle_groups(leg_muscles, exercises_per_workout - 1,
                                                                     exclude=plan_structure[2]['muscles'])) + list(
                            core),
                        'exercises_per_muscle': 1
                    }

        elif goal == 'fat_loss':
            # Для жиросжигания - больше круговых тренировок и кардио
            if days_per_week <= 4:
                # HIIT/Circuit approach
                for day in range(days_per_week):
                    if day % 2 == 0:
                        # Полнотелая круговая тренировка
                        selected_muscle_groups = select_diverse_muscle_groups(all_muscle_groups, exercises_per_workout)
                        plan_structure[day] = {
                            'name': f"Full Body Circuit {day // 2 + 1}",
                            'muscles': selected_muscle_groups,
                            'exercises_per_muscle': 1
                        }
                    else:
                        # День кардио и кора
                        plan_structure[day] = {
                            'name': f"HIIT & Core {day // 2 + 1}",
                            'muscles': list(MuscleGroup.objects.filter(name__in=["Full Body", "Core"])),
                            'exercises_per_muscle': 2
                        }
            else:
                # More targeted approach for 5-6 days
                upper_muscles = MuscleGroup.objects.filter(name__in=["Chest", "Back", "Shoulders", "Arms"])
                lower_muscles = MuscleGroup.objects.filter(name__in=["Legs", "Glutes"])
                core = MuscleGroup.objects.filter(name="Core")
                full_body = MuscleGroup.objects.filter(name="Full Body")

                # День 1: Upper Body Circuit
                plan_structure[0] = {
                    'name': "Upper Body Circuit",
                    'muscles': list(select_diverse_muscle_groups(upper_muscles, exercises_per_workout)),
                    'exercises_per_muscle': 1
                }

                # День 2: Lower Body Circuit
                plan_structure[1] = {
                    'name': "Lower Body Circuit",
                    'muscles': list(select_diverse_muscle_groups(lower_muscles, exercises_per_workout - 1)) + list(
                        core),
                    'exercises_per_muscle': 1
                }

                # День 3: HIIT Cardio
                plan_structure[2] = {
                    'name': "HIIT Cardio",
                    'muscles': list(full_body) + list(core),
                    'exercises_per_muscle': 2
                }

                # День 4: Upper Body Strength
                plan_structure[3] = {
                    'name': "Upper Body Strength",
                    'muscles': list(select_diverse_muscle_groups(upper_muscles, exercises_per_workout,
                                                                 exclude=plan_structure[0]['muscles'])),
                    'exercises_per_muscle': 1
                }

                # День 5: Lower Body Strength
                plan_structure[4] = {
                    'name': "Lower Body Strength",
                    'muscles': list(select_diverse_muscle_groups(lower_muscles, exercises_per_workout - 1,
                                                                 exclude=plan_structure[1]['muscles'])) + list(core),
                    'exercises_per_muscle': 1
                }

                # День 6: Active Recovery
                if days_per_week == 6:
                    plan_structure[5] = {
                        'name': "Active Recovery",
                        'muscles': list(full_body) + list(core),
                        'exercises_per_muscle': 1
                    }

        elif goal == 'strength':
            # Для силы - фокус на базовых упражнениях с тяжелым весом
            if days_per_week <= 3:
                # Основные силовые дни
                if days_per_week >= 1:
                    # День приседаний
                    plan_structure[0] = {
                        'name': "Squat Focus",
                        'muscles': list(MuscleGroup.objects.filter(name__in=["Legs", "Core"])),
                        'exercises_per_muscle': 2
                    }

                if days_per_week >= 2:
                    # День жима
                    plan_structure[1] = {
                        'name': "Bench Focus",
                        'muscles': list(MuscleGroup.objects.filter(name__in=["Chest", "Shoulders", "Arms"])),
                        'exercises_per_muscle': 1
                    }

                if days_per_week == 3:
                    # День становой тяги
                    plan_structure[2] = {
                        'name': "Deadlift Focus",
                        'muscles': list(MuscleGroup.objects.filter(name__in=["Back", "Legs"])),
                        'exercises_per_muscle': 2
                    }

            elif days_per_week == 4:
                # 4-х дневный силовой сплит
                plan_structure[0] = {
                    'name': "Squat Day",
                    'muscles': list(MuscleGroup.objects.filter(name__in=["Legs"])),
                    'exercises_per_muscle': exercises_per_workout
                }
                plan_structure[1] = {
                    'name': "Bench Day",
                    'muscles': list(MuscleGroup.objects.filter(name__in=["Chest", "Arms"])),
                    'exercises_per_muscle': 2
                }
                plan_structure[2] = {
                    'name': "Deadlift Day",
                    'muscles': list(MuscleGroup.objects.filter(name__in=["Back", "Legs"])),
                    'exercises_per_muscle': 2
                }
                plan_structure[3] = {
                    'name': "Overhead Press Day",
                    'muscles': list(MuscleGroup.objects.filter(name__in=["Shoulders", "Arms"])),
                    'exercises_per_muscle': 2
                }

            else:
                # 5-6 дней силовые тренировки с разделением на тяжелые и объемные дни
                plan_structure[0] = {
                    'name': "Squat - Heavy",
                    'muscles': list(MuscleGroup.objects.filter(name__in=["Legs"])),
                    'exercises_per_muscle': 3
                }
                plan_structure[1] = {
                    'name': "Bench - Heavy",
                    'muscles': list(MuscleGroup.objects.filter(name__in=["Chest", "Arms"])),
                    'exercises_per_muscle': 2
                }
                plan_structure[2] = {
                    'name': "Deadlift - Heavy",
                    'muscles': list(MuscleGroup.objects.filter(name__in=["Back"])),
                    'exercises_per_muscle': 3
                }
                plan_structure[3] = {
                    'name': "Squat - Volume",
                    'muscles': list(MuscleGroup.objects.filter(name__in=["Legs"])),
                    'exercises_per_muscle': 2
                }
                plan_structure[4] = {
                    'name': "Bench - Volume",
                    'muscles': list(MuscleGroup.objects.filter(name__in=["Chest", "Arms"])),
                    'exercises_per_muscle': 2
                }
                if days_per_week == 6:
                    plan_structure[5] = {
                        'name': "Deadlift - Volume",
                        'muscles': list(MuscleGroup.objects.filter(name__in=["Back"])),
                        'exercises_per_muscle': 2
                    }

        else:  # general_fitness или endurance
            # Для общего фитнеса - более сбалансированный подход
            if days_per_week <= 3:
                # Полнотелые тренировки для меньшего количества дней
                for day in range(days_per_week):
                    # Для дня общего фитнеса выбираем разнообразные группы мышц
                    selected_muscle_groups = select_diverse_muscle_groups(all_muscle_groups, exercises_per_workout)
                    plan_structure[day] = {
                        'name': f"Full Body Workout {chr(65 + day)}",  # A, B, C и т.д.
                        'muscles': selected_muscle_groups,
                        'exercises_per_muscle': 1
                    }
            else:
                # Для 4+ дней делаем специализированные тренировки
                # День 1: Верх тела
                upper_muscles = MuscleGroup.objects.filter(name__in=["Chest", "Back", "Shoulders", "Arms"])
                plan_structure[0] = {
                    'name': "Upper Body",
                    'muscles': select_diverse_muscle_groups(upper_muscles, exercises_per_workout),
                    'exercises_per_muscle': 1
                }

                # День 2: Низ тела
                lower_muscles = MuscleGroup.objects.filter(name__in=["Legs", "Glutes"])
                core = MuscleGroup.objects.filter(name="Core")
                plan_structure[1] = {
                    'name': "Lower Body",
                    'muscles': list(select_diverse_muscle_groups(lower_muscles, exercises_per_workout - 1)) + list(
                        core),
                    'exercises_per_muscle': 1
                }

                # День 3: Кардио и кор
                plan_structure[2] = {
                    'name': "Cardio & Core",
                    'muscles': list(MuscleGroup.objects.filter(name__in=["Full Body", "Core"])),
                    'exercises_per_muscle': 2
                }

                # День 4: Функциональная тренировка
                if days_per_week >= 4:
                    plan_structure[3] = {
                        'name': "Functional Training",
                        'muscles': select_diverse_muscle_groups(all_muscle_groups, exercises_per_workout),
                        'exercises_per_muscle': 1
                    }

                # День 5: Активное восстановление
                if days_per_week >= 5:
                    plan_structure[4] = {
                        'name': "Active Recovery",
                        'muscles': list(MuscleGroup.objects.filter(name__in=["Full Body"])),
                        'exercises_per_muscle': exercises_per_workout
                    }

                # День 6: Дополнительная тренировка
                if days_per_week == 6:
                    plan_structure[5] = {
                        'name': "Extra Workout",
                        'muscles': select_diverse_muscle_groups(all_muscle_groups, exercises_per_workout,
                                                                exclude=plan_structure[0]['muscles'] +
                                                                        plan_structure[1]['muscles']),
                        'exercises_per_muscle': 1
                    }

        # Установка параметров для выбора упражнений в зависимости от уровня подготовки
        if fitness_level == 'beginner':
            sets_range = "3 x 8-12"
            rest_time = 60
            difficulty_filter = 'beginner'
        elif fitness_level == 'intermediate':
            sets_range = "4 x 8-12"
            rest_time = 90
            difficulty_filter = ['beginner', 'intermediate']
        else:  # advanced
            sets_range = "5 x 6-12"
            rest_time = 120
            difficulty_filter = ['intermediate', 'advanced']

        # Ограничение на максимальное количество упражнений в тренировке
        max_exercises_per_day = 5

        # Добавляем упражнения в план для каждого дня
        for day, day_info in plan_structure.items():
            exercise_order = 0
            total_exercises_today = 0  # Счетчик упражнений в текущий день

            # Для каждой группы мышц выбираем упражнения, но не больше максимального количества на день
            for muscle_group in day_info['muscles']:
                if total_exercises_today >= max_exercises_per_day:
                    break  # Если достигли максимума, останавливаемся

                # Количество упражнений для текущей группы мышц
                exercises_for_this_muscle = min(
                    day_info['exercises_per_muscle'],
                    max_exercises_per_day - total_exercises_today  # Не превышаем общий лимит
                )

                if exercises_for_this_muscle <= 0:
                    continue

                # Фильтруем упражнения по группе мышц и уровню сложности
                if isinstance(difficulty_filter, list):
                    exercises = Exercise.objects.filter(
                        Q(muscle_group=muscle_group) | Q(secondary_muscle_groups=muscle_group),
                        difficulty__in=difficulty_filter
                    ).distinct().order_by('?')
                else:
                    exercises = Exercise.objects.filter(
                        Q(muscle_group=muscle_group) | Q(secondary_muscle_groups=muscle_group),
                        difficulty=difficulty_filter
                    ).distinct().order_by('?')

                # Приоритизируем базовые упражнения для набора массы и силы
                if goal in ['muscle_gain', 'strength']:
                    # Сначала добавляем базовые (compound) упражнения
                    compound_exercises = exercises.filter(is_compound=True)[:exercises_for_this_muscle]
                    for exercise in compound_exercises:
                        PlanExercise.objects.create(
                            workout_plan=plan,
                            exercise=exercise,
                            day_of_week=day,
                            order=exercise_order,
                            sets=int(sets_range.split(' x ')[0]),
                            reps=sets_range.split(' x ')[1],
                            rest_time=rest_time,
                            notes=f"Add weight as you progress"
                        )
                        exercise_order += 1
                        total_exercises_today += 1

                    # Если нужны дополнительные упражнения, добавляем изолирующие
                    if len(compound_exercises) < exercises_for_this_muscle:
                        isolation_count = min(
                            exercises_for_this_muscle - len(compound_exercises),
                            max_exercises_per_day - total_exercises_today
                        )
                        isolation_exercises = exercises.filter(is_compound=False)[:isolation_count]
                        for exercise in isolation_exercises:
                            PlanExercise.objects.create(
                                workout_plan=plan,
                                exercise=exercise,
                                day_of_week=day,
                                order=exercise_order,
                                sets=int(sets_range.split(' x ')[0]),
                                reps=sets_range.split(' x ')[1],
                                rest_time=rest_time
                            )
                            exercise_order += 1
                            total_exercises_today += 1

                # Для жиросжигания и общего фитнеса - смешиваем упражнения
                else:
                    selected_exercises = exercises[:exercises_for_this_muscle]
                    for exercise in selected_exercises:
                        PlanExercise.objects.create(
                            workout_plan=plan,
                            exercise=exercise,
                            day_of_week=day,
                            order=exercise_order,
                            sets=int(sets_range.split(' x ')[0]),
                            reps=sets_range.split(' x ')[1],
                            rest_time=rest_time
                        )
                        exercise_order += 1
                        total_exercises_today += 1

        messages.success(request, "Custom workout plan generated successfully!")
        return redirect('plan_detail', pk=plan.pk)

    context = {
        'goals': goals,
        'fitness_levels': fitness_levels
    }

    return render(request, 'workouts/generate_ai_plan.html', context)


def select_diverse_muscle_groups(all_muscle_groups, count, exclude=None):
    """Выбирает разнообразные группы мышц для сбалансированной тренировки"""
    if exclude is None:
        exclude = []

    # Фильтруем группы мышц, исключая те, что уже использованы
    available_groups = [group for group in all_muscle_groups if group not in exclude]

    # Если групп недостаточно, возвращаем все доступные
    if len(available_groups) <= count:
        return available_groups

    # Иначе выбираем случайные группы
    import random
    return random.sample(available_groups, count)
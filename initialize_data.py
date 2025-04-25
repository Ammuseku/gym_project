#!/usr/bin/env python
"""
Initialize test data for the Gym Optimizer project.
Run this script after migrations to set up sample data.
"""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_optimizer.settings')
django.setup()

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.utils import timezone
from workouts.models import MuscleGroup, Exercise, WorkoutPlan, PlanExercise
from users.models import UserProfile
from datetime import timedelta, date


def create_superuser():
    """Create a superuser if it doesn't exist"""
    try:
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword'
            )
            print("Superuser created successfully.")
        else:
            print("Superuser already exists.")
    except Exception as e:
        print(f"Error creating superuser: {e}")


def create_muscle_groups():
    """Create basic muscle groups"""
    muscle_groups = [
        {"name": "Chest", "description": "Pectoralis major and minor"},
        {"name": "Back", "description": "Latissimus dorsi, rhomboids, trapezius"},
        {"name": "Legs", "description": "Quadriceps, hamstrings, calves"},
        {"name": "Shoulders", "description": "Deltoids (anterior, lateral, posterior)"},
        {"name": "Arms", "description": "Biceps, triceps, forearms"},
        {"name": "Core", "description": "Abdominals, obliques, lower back"},
        {"name": "Glutes", "description": "Gluteus maximus, medius, minimus"},
        {"name": "Full Body", "description": "Compound movements involving multiple muscle groups"},
    ]

    for group in muscle_groups:
        MuscleGroup.objects.get_or_create(
            name=group["name"],
            defaults={"description": group["description"]}
        )

    print(f"Created {len(muscle_groups)} muscle groups.")


def create_exercises():
    """Create basic exercises"""
    # Get muscle groups
    chest = MuscleGroup.objects.get(name="Chest")
    back = MuscleGroup.objects.get(name="Back")
    legs = MuscleGroup.objects.get(name="Legs")
    shoulders = MuscleGroup.objects.get(name="Shoulders")
    arms = MuscleGroup.objects.get(name="Arms")
    core = MuscleGroup.objects.get(name="Core")
    glutes = MuscleGroup.objects.get(name="Glutes")
    full_body = MuscleGroup.objects.get(name="Full Body")

    exercises = [
        # Chest exercises
        {
            "name": "Bench Press",
            "description": "Barbell bench press for chest development",
            "muscle_group": chest,
            "difficulty": "intermediate",
            "category": "strength",
            "instructions": "Lie on a bench, lower the bar to your chest, and press it back up.",
            "equipment_needed": "barbell, bench",
            "is_compound": True
        },
        {
            "name": "Push-ups",
            "description": "Bodyweight exercise for chest, shoulders, and triceps",
            "muscle_group": chest,
            "difficulty": "beginner",
            "category": "strength",
            "instructions": "Start in a plank position and lower your body to the ground, then push back up.",
            "equipment_needed": "none",
            "is_compound": True
        },
        {
            "name": "Dumbbell Fly",
            "description": "Isolation exercise for chest",
            "muscle_group": chest,
            "difficulty": "beginner",
            "category": "strength",
            "instructions": "Lie on a bench with dumbbells, open arms wide, then bring them together above your chest.",
            "equipment_needed": "dumbbells, bench",
            "is_compound": False
        },

        # Back exercises
        {
            "name": "Pull-ups",
            "description": "Bodyweight exercise for back and biceps",
            "muscle_group": back,
            "difficulty": "intermediate",
            "category": "strength",
            "instructions": "Hang from a bar and pull your body up until your chin is above the bar.",
            "equipment_needed": "pull-up bar",
            "is_compound": True
        },
        {
            "name": "Barbell Row",
            "description": "Compound exercise for back development",
            "muscle_group": back,
            "difficulty": "intermediate",
            "category": "strength",
            "instructions": "Bend over with a barbell and pull it towards your lower chest/upper abdomen.",
            "equipment_needed": "barbell",
            "is_compound": True
        },
        {
            "name": "Lat Pulldown",
            "description": "Machine exercise for back width",
            "muscle_group": back,
            "difficulty": "beginner",
            "category": "strength",
            "instructions": "Sit at a lat pulldown machine and pull the bar down to your upper chest.",
            "equipment_needed": "lat pulldown machine",
            "is_compound": False
        },

        # Leg exercises
        {
            "name": "Squats",
            "description": "Compound exercise for overall leg development",
            "muscle_group": legs,
            "difficulty": "intermediate",
            "category": "strength",
            "instructions": "Stand with feet shoulder-width apart, squat down until thighs are parallel to the ground, then stand back up.",
            "equipment_needed": "barbell (optional)",
            "is_compound": True
        },
        {
            "name": "Leg Press",
            "description": "Machine exercise for quadriceps, hamstrings, and glutes",
            "muscle_group": legs,
            "difficulty": "beginner",
            "category": "strength",
            "instructions": "Sit in the machine, press the platform away, then control it back to the starting position.",
            "equipment_needed": "leg press machine",
            "is_compound": True
        },
        {
            "name": "Lunges",
            "description": "Unilateral exercise for legs",
            "muscle_group": legs,
            "difficulty": "beginner",
            "category": "strength",
            "instructions": "Step forward with one leg, lower your body, then push back to the starting position.",
            "equipment_needed": "dumbbells (optional)",
            "is_compound": True
        },

        # Shoulder exercises
        {
            "name": "Overhead Press",
            "description": "Compound exercise for shoulder development",
            "muscle_group": shoulders,
            "difficulty": "intermediate",
            "category": "strength",
            "instructions": "Press the weight from shoulder level to overhead.",
            "equipment_needed": "barbell or dumbbells",
            "is_compound": True
        },
        {
            "name": "Lateral Raises",
            "description": "Isolation exercise for lateral deltoids",
            "muscle_group": shoulders,
            "difficulty": "beginner",
            "category": "strength",
            "instructions": "Raise dumbbells to the sides until arms are parallel to the ground.",
            "equipment_needed": "dumbbells",
            "is_compound": False
        },

        # Arm exercises
        {
            "name": "Bicep Curls",
            "description": "Isolation exercise for biceps",
            "muscle_group": arms,
            "difficulty": "beginner",
            "category": "strength",
            "instructions": "Curl the weight from a hanging position up to your shoulders.",
            "equipment_needed": "dumbbells or barbell",
            "is_compound": False
        },
        {
            "name": "Tricep Dips",
            "description": "Bodyweight or assisted exercise for triceps",
            "muscle_group": arms,
            "difficulty": "intermediate",
            "category": "strength",
            "instructions": "Lower your body by bending your elbows, then press back up.",
            "equipment_needed": "dip bars or bench",
            "is_compound": False
        },

        # Core exercises
        {
            "name": "Planks",
            "description": "Isometric exercise for core stability",
            "muscle_group": core,
            "difficulty": "beginner",
            "category": "strength",
            "instructions": "Hold a push-up position with elbows on the ground, keeping body straight.",
            "equipment_needed": "none",
            "is_compound": False
        },
        {
            "name": "Russian Twists",
            "description": "Rotational exercise for obliques",
            "muscle_group": core,
            "difficulty": "beginner",
            "category": "strength",
            "instructions": "Sit with knees bent, twist torso side to side.",
            "equipment_needed": "weight (optional)",
            "is_compound": False
        },

        # Full body exercises
        {
            "name": "Deadlift",
            "description": "Compound exercise for overall strength",
            "muscle_group": full_body,
            "difficulty": "advanced",
            "category": "strength",
            "instructions": "Lift a barbell from the ground to hip level, keeping back straight.",
            "equipment_needed": "barbell",
            "is_compound": True
        },
        {
            "name": "Burpees",
            "description": "High-intensity exercise for conditioning",
            "muscle_group": full_body,
            "difficulty": "intermediate",
            "category": "cardio",
            "instructions": "From standing, drop to a push-up position, perform a push-up, jump feet toward hands, and jump up.",
            "equipment_needed": "none",
            "is_compound": True
        }
    ]

    created_count = 0
    for exercise_data in exercises:
        exercise, created = Exercise.objects.get_or_create(
            name=exercise_data["name"],
            defaults=exercise_data
        )
        if created:
            created_count += 1

    print(f"Created {created_count} exercises.")


def create_sample_workout_plans():
    """Create sample workout plans"""
    # Get admin user
    try:
        admin = User.objects.get(username='admin')
    except User.DoesNotExist:
        print("Admin user not found. Please create a superuser first.")
        return

    plans = [
        {
            "name": "Beginner Full Body",
            "description": "A 3-day full body workout for beginners",
            "goal": "general_fitness",
            "intensity": "low",
            "duration_weeks": 8,
            "is_public": True
        },
        {
            "name": "Intermediate Push/Pull/Legs",
            "description": "A 6-day push/pull/legs split for intermediate lifters",
            "goal": "muscle_gain",
            "intensity": "medium",
            "duration_weeks": 12,
            "is_public": True
        },
        {
            "name": "Advanced Strength Program",
            "description": "A 4-day strength-focused program",
            "goal": "strength",
            "intensity": "high",
            "duration_weeks": 16,
            "is_public": True
        }
    ]

    created_count = 0
    for plan_data in plans:
        plan, created = WorkoutPlan.objects.get_or_create(
            name=plan_data["name"],
            defaults={**plan_data, "created_by": admin}
        )
        if created:
            created_count += 1

            # Add some exercises to the beginner plan
            if plan.name == "Beginner Full Body":
                # Day 1 (Monday)
                create_plan_exercises(plan, 0, [
                    {"name": "Squats", "sets": 3, "reps": "8-10", "order": 1},
                    {"name": "Push-ups", "sets": 3, "reps": "8-12", "order": 2},
                    {"name": "Barbell Row", "sets": 3, "reps": "8-10", "order": 3},
                    {"name": "Planks", "sets": 3, "reps": "30-60 seconds", "order": 4}
                ])

                # Day 3 (Wednesday)
                create_plan_exercises(plan, 2, [
                    {"name": "Lunges", "sets": 3, "reps": "10-12 per leg", "order": 1},
                    {"name": "Overhead Press", "sets": 3, "reps": "8-10", "order": 2},
                    {"name": "Pull-ups", "sets": 3, "reps": "as many as possible", "order": 3},
                    {"name": "Russian Twists", "sets": 3, "reps": "15-20 per side", "order": 4}
                ])

                # Day 5 (Friday)
                create_plan_exercises(plan, 4, [
                    {"name": "Deadlift", "sets": 3, "reps": "6-8", "order": 1},
                    {"name": "Bench Press", "sets": 3, "reps": "8-10", "order": 2},
                    {"name": "Lat Pulldown", "sets": 3, "reps": "10-12", "order": 3},
                    {"name": "Bicep Curls", "sets": 3, "reps": "10-12", "order": 4}
                ])

    print(f"Created {created_count} workout plans.")


def create_plan_exercises(plan, day_of_week, exercises):
    """Helper function to create exercises for a plan"""
    for exercise_data in exercises:
        exercise = Exercise.objects.get(name=exercise_data["name"])
        PlanExercise.objects.create(
            workout_plan=plan,
            exercise=exercise,
            day_of_week=day_of_week,
            order=exercise_data["order"],
            sets=exercise_data["sets"],
            reps=exercise_data["reps"],
            rest_time=60
        )


def main():
    """Run all initialization functions"""
    print("Initializing data for Gym Optimizer...")

    create_superuser()
    create_muscle_groups()
    create_exercises()
    create_sample_workout_plans()

    print("Data initialization complete.")


if __name__ == "__main__":
    main()
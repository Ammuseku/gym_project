from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class MuscleGroup(models.Model):
    """Model representing different muscle groups (e.g. Chest, Back, Legs)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='muscle_groups/', blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_exercise_count(self):
        """Get count of exercises for this muscle group"""
        return self.exercises.count()


class Exercise(models.Model):
    """Model representing individual exercises"""
    DIFFICULTY_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )

    CATEGORY_CHOICES = (
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibility'),
        ('balance', 'Balance'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField()
    muscle_group = models.ForeignKey(MuscleGroup, on_delete=models.CASCADE, related_name='exercises')
    secondary_muscle_groups = models.ManyToManyField(MuscleGroup, related_name='secondary_exercises', blank=True)
    difficulty = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES, default='beginner')
    category = models.CharField(max_length=15, choices=CATEGORY_CHOICES, default='strength')
    instructions = models.TextField()
    video_url = models.URLField(blank=True)
    image = models.ImageField(upload_to='exercises/', blank=True, null=True)
    equipment_needed = models.CharField(max_length=255, blank=True)
    is_compound = models.BooleanField(default=False, help_text="Is this a compound exercise?")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('exercise_detail', args=[str(self.id)])

    def get_average_weight(self, user):
        """Get average weight used by this user for this exercise"""
        logs = UserPlanExercise.objects.filter(
            user=user,
            plan_exercise__exercise=self,
            weight__isnull=False
        )
        if logs.count() == 0:
            return None
        return sum(log.weight for log in logs) / logs.count()


class WorkoutPlan(models.Model):
    """Model representing workout plans"""
    GOAL_CHOICES = (
        ('muscle_gain', 'Muscle Gain'),
        ('fat_loss', 'Fat Loss'),
        ('strength', 'Strength'),
        ('endurance', 'Endurance'),
        ('general_fitness', 'General Fitness'),
    )

    INTENSITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField()
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    intensity = models.CharField(max_length=10, choices=INTENSITY_CHOICES)
    duration_weeks = models.PositiveIntegerField(default=4)
    is_public = models.BooleanField(default=False, help_text="Make this plan available to all users")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('plan_detail', args=[str(self.id)])

    def get_exercise_count(self):
        """Get count of unique exercises in this plan"""
        return PlanExercise.objects.filter(workout_plan=self).values('exercise').distinct().count()

    def get_weekly_workouts(self):
        """Group exercises by week day for this plan"""
        exercises = PlanExercise.objects.filter(workout_plan=self).order_by('day_of_week')
        weeks = {}
        for ex in exercises:
            if ex.day_of_week not in weeks:
                weeks[ex.day_of_week] = []
            weeks[ex.day_of_week].append(ex)
        return weeks

    def is_followed_by(self, user):
        """Check if this plan is followed by the given user"""
        return UserWorkoutPlan.objects.filter(workout_plan=self, user=user).exists()


class PlanExercise(models.Model):
    """Model linking exercises to workout plans with sets, reps, etc."""
    DAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )

    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    order = models.PositiveIntegerField(default=0)
    sets = models.PositiveIntegerField(default=3)
    reps = models.CharField(max_length=20, default='10', help_text="Reps per set, e.g., '10' or '8-12'")
    rest_time = models.PositiveIntegerField(default=60, help_text="Rest time in seconds")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['day_of_week', 'order']

    def __str__(self):
        return f"{self.exercise.name} - {self.get_day_of_week_display()} - {self.workout_plan.name}"


class UserWorkoutPlan(models.Model):
    """Model representing a user's active workout plans"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_plans')
    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='users')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = ['user', 'workout_plan']

    def __str__(self):
        return f"{self.user.username} - {self.workout_plan.name}"

    def save(self, *args, **kwargs):
        # Set end date if not provided
        if not self.end_date and self.start_date:
            from datetime import timedelta
            self.end_date = self.start_date + timedelta(weeks=self.workout_plan.duration_weeks)
        super().save(*args, **kwargs)

    def get_progress_percentage(self):
        """Calculate percentage of completed workouts"""
        total_workouts = self.workout_plan.get_exercise_count() * self.workout_plan.duration_weeks
        if total_workouts == 0:
            return 0

        completed_workouts = UserPlanExercise.objects.filter(
            user=self.user,
            plan_exercise__workout_plan=self.workout_plan,
            completed=True
        ).count()

        return (completed_workouts / total_workouts) * 100


class UserPlanExercise(models.Model):
    """Model tracking user's actual performance for each exercise in their plan"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_logs')
    plan_exercise = models.ForeignKey(PlanExercise, on_delete=models.CASCADE, related_name='user_logs')
    date = models.DateField(default=timezone.now)
    weight = models.FloatField(null=True, blank=True, help_text="Weight used (in kg)")
    completed_sets = models.PositiveIntegerField(default=0)
    completed_reps = models.CharField(max_length=50, blank=True,
                                      help_text="Actual reps completed per set, e.g. '10,8,8'")
    perceived_difficulty = models.IntegerField(null=True, blank=True, help_text="Rate from 1-10")
    notes = models.TextField(blank=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.plan_exercise.exercise.name} - {self.date}"

    def get_progress(self):
        """Calculate progress compared to previous log"""
        previous_log = UserPlanExercise.objects.filter(
            user=self.user,
            plan_exercise__exercise=self.plan_exercise.exercise,
            date__lt=self.date
        ).order_by('-date').first()

        if not previous_log or not previous_log.weight or not self.weight:
            return None

        return ((self.weight - previous_log.weight) / previous_log.weight) * 100

    def get_weight_suggestion(self):
        """Suggest weight for next workout based on perceived difficulty"""
        if not self.weight or self.perceived_difficulty is None:
            return None

        if self.perceived_difficulty <= 3:  # Too easy
            return self.weight * 1.1  # Increase by 10%
        elif self.perceived_difficulty <= 7:  # Appropriate
            return self.weight * 1.05  # Increase by 5%
        else:  # Too difficult
            return self.weight * 0.95  # Decrease by 5%


class WorkoutSchedule(models.Model):
    """Model for scheduling workouts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    day_of_week = models.IntegerField(choices=PlanExercise.DAY_CHOICES)
    completed = models.BooleanField(default=False)
    notification_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.user.username} - {self.workout_plan.name} - {self.date}"

    def get_exercises(self):
        """Get exercises for this scheduled workout"""
        return PlanExercise.objects.filter(
            workout_plan=self.workout_plan,
            day_of_week=self.day_of_week
        ).order_by('order')

    def mark_as_completed(self):
        """Mark this workout as completed"""
        self.completed = True
        self.save()

        # Also mark all exercises as completed
        for exercise in self.get_exercises():
            UserPlanExercise.objects.update_or_create(
                user=self.user,
                plan_exercise=exercise,
                date=self.date,
                defaults={'completed': True}
            )
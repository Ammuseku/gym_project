from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class BodyMetrics(models.Model):
    """Model for tracking various body measurements and metrics"""
    METRIC_TYPES = (
        ('weight', 'Weight'),
        ('body_fat', 'Body Fat Percentage'),
        ('muscle_mass', 'Muscle Mass'),
        ('chest', 'Chest Measurement'),
        ('waist', 'Waist Measurement'),
        ('hips', 'Hips Measurement'),
        ('thigh', 'Thigh Measurement'),
        ('arm', 'Arm Measurement'),
        ('other', 'Other')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='body_metrics')
    date = models.DateField(default=timezone.now)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    value = models.FloatField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', 'metric_type']
        verbose_name_plural = 'Body Metrics'

    def __str__(self):
        return f"{self.user.username} - {self.get_metric_type_display()} - {self.date}"

    def get_previous(self):
        """Get previous measurement for this metric type"""
        return BodyMetrics.objects.filter(
            user=self.user,
            metric_type=self.metric_type,
            date__lt=self.date
        ).order_by('-date').first()

    def get_change(self):
        """Calculate change from previous measurement"""
        previous = self.get_previous()
        if not previous:
            return None
        return self.value - previous.value

    def get_percent_change(self):
        """Calculate percentage change from previous measurement"""
        previous = self.get_previous()
        if not previous or previous.value == 0:
            return None
        return ((self.value - previous.value) / previous.value) * 100


class WorkoutLog(models.Model):
    """Model for tracking completed workouts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_logs')
    date = models.DateField(default=timezone.now)
    workout_name = models.CharField(max_length=100, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in minutes")
    calories_burned = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # Fields for automatic tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.workout_name or 'Workout'} - {self.date}"

    def get_exercises(self):
        """Get exercises completed in this workout"""
        from workouts.models import UserPlanExercise
        return UserPlanExercise.objects.filter(
            user=self.user,
            date=self.date
        ).select_related('plan_exercise__exercise')


class Goal(models.Model):
    """Model for tracking fitness goals"""
    GOAL_TYPES = (
        ('weight', 'Weight Goal'),
        ('body_fat', 'Body Fat Percentage Goal'),
        ('strength', 'Strength Goal'),
        ('endurance', 'Endurance Goal'),
        ('habit', 'Habit Goal'),
        ('other', 'Other Goal')
    )

    STATUS_CHOICES = (
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    target_value = models.FloatField(null=True, blank=True, help_text="Target numerical value if applicable")
    target_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='not_started')

    # For strength goals
    exercise = models.ForeignKey('workouts.Exercise', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['target_date', 'start_date']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def get_progress_percentage(self):
        """Calculate percentage progress towards goal"""
        if self.goal_type in ['weight', 'body_fat'] and self.target_value is not None:
            # Get latest metric
            latest_metric = BodyMetrics.objects.filter(
                user=self.user,
                metric_type=self.goal_type
            ).order_by('-date').first()

            if not latest_metric:
                return 0

            # Get initial metric
            initial_metric = BodyMetrics.objects.filter(
                user=self.user,
                metric_type=self.goal_type,
                date__lte=self.start_date
            ).order_by('-date').first()

            if not initial_metric:
                initial_metric = latest_metric

            # Calculate progress
            total_change_needed = self.target_value - initial_metric.value

            if total_change_needed == 0:
                return 100  # Already at goal

            current_change = latest_metric.value - initial_metric.value
            progress = (current_change / total_change_needed) * 100

            # Cap progress at 100%
            return min(max(progress, 0), 100)

        elif self.goal_type == 'strength' and self.target_value is not None and self.exercise:
            # For strength goals, check latest weight used
            from workouts.models import UserPlanExercise
            latest_log = UserPlanExercise.objects.filter(
                user=self.user,
                plan_exercise__exercise=self.exercise,
                weight__isnull=False
            ).order_by('-date').first()

            if not latest_log:
                return 0

            # Get initial weight
            initial_log = UserPlanExercise.objects.filter(
                user=self.user,
                plan_exercise__exercise=self.exercise,
                weight__isnull=False,
                date__lte=self.start_date
            ).order_by('-date').first()

            if not initial_log:
                initial_log = latest_log

            # Calculate progress
            total_increase_needed = self.target_value - initial_log.weight

            if total_increase_needed <= 0:
                return 100  # Already at goal

            current_increase = latest_log.weight - initial_log.weight
            progress = (current_increase / total_increase_needed) * 100

            # Cap progress at 100%
            return min(max(progress, 0), 100)

        # For other goal types, return manual progress
        elif self.status == 'completed':
            return 100
        elif self.status == 'in_progress':
            # Calculate time-based progress if target date exists
            if self.target_date:
                total_days = (self.target_date - self.start_date).days
                if total_days <= 0:
                    return 50  # Default to 50% if dates are invalid

                days_passed = (timezone.now().date() - self.start_date).days
                time_progress = (days_passed / total_days) * 100
                return min(time_progress, 99)  # Cap at 99% until completed
            return 50  # Default to 50% for in-progress goals
        elif self.status == 'not_started':
            return 0
        else:  # abandoned
            return 0


class Milestone(models.Model):
    """Model for tracking fitness milestones and achievements"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date_achieved = models.DateField(default=timezone.now)

    # Optional fields
    exercise = models.ForeignKey('workouts.Exercise', on_delete=models.SET_NULL, null=True, blank=True)
    weight = models.FloatField(null=True, blank=True, help_text="Weight achieved (if applicable)")
    reps = models.PositiveIntegerField(null=True, blank=True, help_text="Reps achieved (if applicable)")

    class Meta:
        ordering = ['-date_achieved']

    def __str__(self):
        return f"{self.user.username} - {self.title} - {self.date_achieved}"
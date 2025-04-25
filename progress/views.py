from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Avg, Max, Min
from datetime import timedelta
from .models import BodyMetrics, WorkoutLog, Goal, Milestone
from django.db.models import Avg, Max, Min, Sum
from .forms import (
    BodyMetricsForm, WorkoutLogForm, GoalForm, MilestoneForm,
    DateRangeForm, MetricsFilterForm
)
from workouts.models import UserPlanExercise


@login_required
def progress_tracking(request):
    """Main progress tracking dashboard"""
    # Get recent metrics
    recent_metrics = BodyMetrics.objects.filter(
        user=request.user
    ).order_by('-date', 'metric_type')[:10]

    # Get recent workout logs
    recent_workouts = WorkoutLog.objects.filter(
        user=request.user
    ).order_by('-date')[:5]

    # Get active goals
    active_goals = Goal.objects.filter(
        user=request.user,
        status__in=['not_started', 'in_progress']
    ).order_by('target_date')

    # Get recent milestones
    recent_milestones = Milestone.objects.filter(
        user=request.user
    ).order_by('-date_achieved')[:3]

    # Get weight history for chart
    weight_history = BodyMetrics.objects.filter(
        user=request.user,
        metric_type='weight'
    ).order_by('date')

    # Get body fat history for chart
    body_fat_history = BodyMetrics.objects.filter(
        user=request.user,
        metric_type='body_fat'
    ).order_by('date')

    context = {
        'recent_metrics': recent_metrics,
        'recent_workouts': recent_workouts,
        'active_goals': active_goals,
        'recent_milestones': recent_milestones,
        'weight_history': weight_history,
        'body_fat_history': body_fat_history,
    }

    return render(request, 'progress/progress_tracking.html', context)


@login_required
def log_progress(request):
    """View for logging new body metrics"""
    if request.method == 'POST':
        form = BodyMetricsForm(request.POST)
        if form.is_valid():
            metrics = form.save(commit=False)
            metrics.user = request.user
            metrics.save()

            messages.success(request, f"Your {metrics.get_metric_type_display()} has been logged successfully!")

            # Redirect back to the form with the same metric type pre-selected
            return redirect('log_progress')
    else:
        # Pre-select the metric type if provided in URL
        initial = {}
        metric_type = request.GET.get('metric_type')
        if metric_type:
            initial['metric_type'] = metric_type

        form = BodyMetricsForm(initial=initial)

    # Get recent metrics for the same type
    metric_type = request.GET.get('metric_type', 'weight')
    recent_metrics = BodyMetrics.objects.filter(
        user=request.user,
        metric_type=metric_type
    ).order_by('-date')[:5]

    context = {
        'form': form,
        'recent_metrics': recent_metrics,
        'metric_type': metric_type
    }

    return render(request, 'progress/log_progress.html', context)


@login_required
def metrics_history(request):
    """View for displaying metrics history with filtering"""
    # Create filter forms
    date_form = DateRangeForm(request.GET)
    metric_form = MetricsFilterForm(request.GET)

    # Get all metrics for user
    metrics = BodyMetrics.objects.filter(user=request.user).order_by('-date')

    # Apply filters if forms are valid
    if date_form.is_valid() and metric_form.is_valid():
        # Apply date range filter
        start_date = date_form.cleaned_data.get('start_date')
        end_date = date_form.cleaned_data.get('end_date')

        if start_date:
            metrics = metrics.filter(date__gte=start_date)

        if end_date:
            metrics = metrics.filter(date__lte=end_date)

        # Apply metric type filter
        metric_type = metric_form.cleaned_data.get('metric_type')
        if metric_type and metric_type != 'all':
            metrics = metrics.filter(metric_type=metric_type)

    # Group metrics by type for summary stats
    metric_types = set([m.metric_type for m in metrics])
    summary = {}

    for metric_type in metric_types:
        type_metrics = metrics.filter(metric_type=metric_type)

        if type_metrics.exists():
            latest = type_metrics.first()
            oldest = type_metrics.order_by('date').first()

            summary[metric_type] = {
                'latest': latest,
                'oldest': oldest,
                'change': latest.value - oldest.value if oldest else 0,
                'percent_change': (
                            (latest.value - oldest.value) / oldest.value * 100) if oldest and oldest.value != 0 else 0
            }

    context = {
        'metrics': metrics,
        'summary': summary,
        'date_form': date_form,
        'metric_form': metric_form
    }

    return render(request, 'progress/metrics_history.html', context)


@login_required
def delete_metric(request, pk):
    """Delete a body metric record"""
    metric = get_object_or_404(BodyMetrics, pk=pk, user=request.user)

    if request.method == 'POST':
        metric_type = metric.get_metric_type_display()
        metric.delete()
        messages.success(request, f"Your {metric_type} record has been deleted.")
        return redirect('metrics_history')

    return render(request, 'progress/confirm_delete_metric.html', {'metric': metric})


@login_required
def workout_history(request):
    """View for displaying workout history"""
    # Create date range filter form
    form = DateRangeForm(request.GET)

    # Get all workout logs for user
    workouts = WorkoutLog.objects.filter(user=request.user).order_by('-date')

    # Apply date filters if form is valid
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')

        if start_date:
            workouts = workouts.filter(date__gte=start_date)

        if end_date:
            workouts = workouts.filter(date__lte=end_date)

    # Calculate summary stats
    total_workouts = workouts.count()
    total_minutes = workouts.aggregate(total=Sum('duration'))['total'] or 0

    # Get workout history by month for chart
    months = {}
    for workout in workouts:
        month_key = workout.date.strftime('%Y-%m')
        if month_key not in months:
            months[month_key] = {'count': 0, 'duration': 0}

        months[month_key]['count'] += 1
        if workout.duration:
            months[month_key]['duration'] += workout.duration

    context = {
        'workouts': workouts,
        'form': form,
        'total_workouts': total_workouts,
        'total_minutes': total_minutes,
        'months': months
    }

    return render(request, 'progress/workout_history.html', context)


@login_required
def log_workout(request):
    """View for logging workout manually"""
    if request.method == 'POST':
        form = WorkoutLogForm(request.POST)
        if form.is_valid():
            workout = form.save(commit=False)
            workout.user = request.user
            workout.save()

            messages.success(request, "Your workout has been logged successfully!")
            return redirect('workout_history')
    else:
        # Pre-fill today's date
        form = WorkoutLogForm(initial={'date': timezone.now().date()})

    context = {'form': form}
    return render(request, 'progress/log_workout.html', context)


@login_required
def workout_detail(request, pk):
    """View for displaying workout details"""
    workout = get_object_or_404(WorkoutLog, pk=pk, user=request.user)

    # Get exercises for this workout
    exercises = UserPlanExercise.objects.filter(
        user=request.user,
        date=workout.date
    ).select_related('plan_exercise__exercise')

    context = {
        'workout': workout,
        'exercises': exercises
    }

    return render(request, 'progress/workout_detail.html', context)


@login_required
def delete_workout(request, pk):
    """Delete a workout log"""
    workout = get_object_or_404(WorkoutLog, pk=pk, user=request.user)

    if request.method == 'POST':
        workout.delete()
        messages.success(request, "Your workout log has been deleted.")
        return redirect('workout_history')

    return render(request, 'progress/confirm_delete_workout.html', {'workout': workout})


@login_required
def goals(request):
    """View for displaying and managing goals"""
    # Get goals by status
    active_goals = Goal.objects.filter(
        user=request.user,
        status__in=['not_started', 'in_progress']
    ).order_by('target_date')

    completed_goals = Goal.objects.filter(
        user=request.user,
        status='completed'
    ).order_by('-target_date')

    abandoned_goals = Goal.objects.filter(
        user=request.user,
        status='abandoned'
    ).order_by('-target_date')

    context = {
        'active_goals': active_goals,
        'completed_goals': completed_goals,
        'abandoned_goals': abandoned_goals
    }

    return render(request, 'progress/goals.html', context)


@login_required
def create_goal(request):
    """View for creating a new goal"""
    if request.method == 'POST':
        form = GoalForm(request.POST, user=request.user)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()

            messages.success(request, "Your goal has been created successfully!")
            return redirect('goals')
    else:
        # Pre-fill today's date as start date
        form = GoalForm(initial={'start_date': timezone.now().date()}, user=request.user)

    context = {'form': form}
    return render(request, 'progress/goal_form.html', context)


@login_required
def edit_goal(request, pk):
    """View for editing an existing goal"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    if request.method == 'POST':
        form = GoalForm(request.POST, instance=goal, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your goal has been updated successfully!")
            return redirect('goals')
    else:
        form = GoalForm(instance=goal, user=request.user)

    context = {
        'form': form,
        'goal': goal,
        'is_edit': True
    }

    return render(request, 'progress/goal_form.html', context)


@login_required
def delete_goal(request, pk):
    """Delete a goal"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    if request.method == 'POST':
        goal.delete()
        messages.success(request, "Your goal has been deleted.")
        return redirect('goals')

    return render(request, 'progress/confirm_delete_goal.html', {'goal': goal})


@login_required
def milestones(request):
    """View for displaying milestones"""
    user_milestones = Milestone.objects.filter(
        user=request.user
    ).order_by('-date_achieved')

    context = {'milestones': user_milestones}
    return render(request, 'progress/milestones.html', context)


@login_required
def create_milestone(request):
    """View for creating a new milestone"""
    if request.method == 'POST':
        form = MilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.user = request.user
            milestone.save()

            messages.success(request, "Your milestone has been recorded successfully!")
            return redirect('milestones')
    else:
        # Pre-fill today's date
        form = MilestoneForm(initial={'date_achieved': timezone.now().date()})

    context = {'form': form}
    return render(request, 'progress/milestone_form.html', context)


@login_required
def delete_milestone(request, pk):
    """Delete a milestone"""
    milestone = get_object_or_404(Milestone, pk=pk, user=request.user)

    if request.method == 'POST':
        milestone.delete()
        messages.success(request, "Your milestone has been deleted.")
        return redirect('milestones')

    return render(request, 'progress/confirm_delete_milestone.html', {'milestone': milestone})


@login_required
def analytics(request):
    """View for displaying detailed analytics and charts"""
    # Get date range for filtering
    form = DateRangeForm(request.GET)

    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=90)  # Default to last 90 days

    if form.is_valid():
        if form.cleaned_data.get('start_date'):
            start_date = form.cleaned_data.get('start_date')

        if form.cleaned_data.get('end_date'):
            end_date = form.cleaned_data.get('end_date')

    # Get metrics data for charts
    weight_data = BodyMetrics.objects.filter(
        user=request.user,
        metric_type='weight',
        date__range=[start_date, end_date]
    ).order_by('date')

    body_fat_data = BodyMetrics.objects.filter(
        user=request.user,
        metric_type='body_fat',
        date__range=[start_date, end_date]
    ).order_by('date')

    # Get workout data for charts
    workout_data = WorkoutLog.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).order_by('date')

    # Calculate summary stats
    stats = {
        'total_workouts': workout_data.count(),
        'avg_duration': workout_data.aggregate(avg=Avg('duration'))['avg'],
        'max_duration': workout_data.aggregate(max=Max('duration'))['max'],
        'total_duration': workout_data.aggregate(Sum('duration'))['duration__sum'],
    }

    if weight_data.exists():
        latest_weight = weight_data.latest('date')
        earliest_weight = weight_data.earliest('date')

        stats['latest_weight'] = latest_weight.value
        stats['weight_change'] = latest_weight.value - earliest_weight.value
        stats['weight_change_percent'] = (stats[
                                              'weight_change'] / earliest_weight.value) * 100 if earliest_weight.value != 0 else 0

    if body_fat_data.exists():
        latest_bf = body_fat_data.latest('date')
        earliest_bf = body_fat_data.earliest('date')

        stats['latest_body_fat'] = latest_bf.value
        stats['body_fat_change'] = latest_bf.value - earliest_bf.value

    context = {
        'form': form,
        'stats': stats,
        'weight_data': weight_data,
        'body_fat_data': body_fat_data,
        'workout_data': workout_data,
        'start_date': start_date,
        'end_date': end_date
    }

    return render(request, 'progress/analytics.html', context)


@login_required
def get_chart_data(request):
    """API endpoint for getting chart data in JSON format"""
    metric_type = request.GET.get('metric_type', 'weight')
    days = int(request.GET.get('days', 90))

    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    if metric_type in ['weight', 'body_fat', 'muscle_mass']:
        # Get body metrics data
        data = BodyMetrics.objects.filter(
            user=request.user,
            metric_type=metric_type,
            date__range=[start_date, end_date]
        ).order_by('date')

        result = [
            {
                'date': item.date.strftime('%Y-%m-%d'),
                'value': item.value
            }
            for item in data
        ]

    elif metric_type == 'workouts':
        # Get workout count by day
        workouts = WorkoutLog.objects.filter(
            user=request.user,
            date__range=[start_date, end_date]
        ).order_by('date')

        # Group by date
        result = {}
        for workout in workouts:
            date_str = workout.date.strftime('%Y-%m-%d')
            if date_str not in result:
                result[date_str] = 0
            result[date_str] += 1

        result = [
            {
                'date': date,
                'value': count
            }
            for date, count in result.items()
        ]

    elif metric_type == 'duration':
        # Get workout duration by day
        workouts = WorkoutLog.objects.filter(
            user=request.user,
            date__range=[start_date, end_date],
            duration__isnull=False
        ).order_by('date')

        # Group by date
        result = {}
        for workout in workouts:
            date_str = workout.date.strftime('%Y-%m-%d')
            if date_str not in result:
                result[date_str] = 0
            result[date_str] += workout.duration

        result = [
            {
                'date': date,
                'value': duration
            }
            for date, duration in result.items()
        ]

    else:
        result = []

    return JsonResponse(result, safe=False)
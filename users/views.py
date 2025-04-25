from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, UserUpdateForm, ProfileUpdateForm
from .models import UserProfile
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('account_login')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_progress': get_user_progress(request.user)
    }

    return render(request, 'users/profile.html', context)


@login_required
def settings(request):
    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Your settings have been updated!')
            return redirect('settings')
    else:
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'profile_form': profile_form,
    }

    return render(request, 'users/settings.html', context)


@login_required
def connect_google_fit(request):
    # This would be implemented with Google OAuth2 flow
    # For now we'll just simulate a connection
    profile = request.user.profile
    profile.google_fit_connected = True
    profile.save()

    messages.success(request, 'Successfully connected to Google Fit!')
    return redirect('settings')


@login_required
def disconnect_google_fit(request):
    profile = request.user.profile
    profile.google_fit_connected = False
    profile.save()

    messages.success(request, 'Successfully disconnected from Google Fit!')
    return redirect('settings')


@login_required
def connect_apple_health(request):
    # This would be implemented with Apple HealthKit
    # For now we'll just simulate a connection
    profile = request.user.profile
    profile.apple_health_connected = True
    profile.save()

    messages.success(request, 'Successfully connected to Apple Health!')
    return redirect('settings')


@login_required
def disconnect_apple_health(request):
    profile = request.user.profile
    profile.apple_health_connected = False
    profile.save()

    messages.success(request, 'Successfully disconnected from Apple Health!')
    return redirect('settings')


def get_user_progress(user):
    """Helper function to get user's recent progress for profile page"""
    from progress.models import BodyMetrics, WorkoutLog

    # Get recent body metrics
    recent_weight = BodyMetrics.objects.filter(
        user=user,
        metric_type='weight'
    ).order_by('-date').first()

    recent_body_fat = BodyMetrics.objects.filter(
        user=user,
        metric_type='body_fat'
    ).order_by('-date').first()

    # Get recent workout stats
    workout_count = WorkoutLog.objects.filter(user=user).count()
    last_workout = WorkoutLog.objects.filter(user=user).order_by('-date').first()

    return {
        'recent_weight': recent_weight,
        'recent_body_fat': recent_body_fat,
        'workout_count': workout_count,
        'last_workout': last_workout
    }
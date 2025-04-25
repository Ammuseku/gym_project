from django import forms
from .models import BodyMetrics, WorkoutLog, Goal, Milestone
from django.utils import timezone
from django.core.exceptions import ValidationError


class BodyMetricsForm(forms.ModelForm):
    class Meta:
        model = BodyMetrics
        fields = ['metric_type', 'value', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'max': timezone.now().date()}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set max date to current date
        self.fields['date'].widget.attrs['max'] = timezone.now().date().isoformat()

    def clean_value(self):
        value = self.cleaned_data.get('value')
        metric_type = self.cleaned_data.get('metric_type')

        # Validate ranges for different metric types
        if metric_type == 'weight':
            if value <= 0 or value > 500:
                raise ValidationError("Weight must be between 0 and 500 kg.")
        elif metric_type == 'body_fat':
            if value < 0 or value > 50:
                raise ValidationError("Body fat percentage must be between 0 and 50%.")
        elif metric_type in ['chest', 'waist', 'hips', 'thigh', 'arm']:
            if value <= 0 or value > 200:
                raise ValidationError("Measurement must be between 0 and 200 cm.")

        return value


class WorkoutLogForm(forms.ModelForm):
    class Meta:
        model = WorkoutLog
        fields = ['date', 'workout_name', 'duration', 'calories_burned', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'max': timezone.now().date()}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set max date to current date
        self.fields['date'].widget.attrs['max'] = timezone.now().date().isoformat()


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = [
            'goal_type', 'title', 'description', 'target_value',
            'start_date', 'target_date', 'status', 'exercise'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'target_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set min date for start_date to avoid back-dating too far
        min_date = (timezone.now() - timezone.timedelta(days=30)).date().isoformat()
        self.fields['start_date'].widget.attrs['min'] = min_date

        # Set min date for target_date to today
        self.fields['target_date'].widget.attrs['min'] = timezone.now().date().isoformat()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        target_date = cleaned_data.get('target_date')
        goal_type = cleaned_data.get('goal_type')
        exercise = cleaned_data.get('exercise')
        target_value = cleaned_data.get('target_value')

        # Check if target date is after start date
        if start_date and target_date and start_date > target_date:
            raise ValidationError("Target date must be after start date.")

        # Validate exercise is provided for strength goals
        if goal_type == 'strength' and not exercise:
            raise ValidationError({
                'exercise': "Exercise is required for strength goals."
            })

        # Validate target value for numeric goals
        if goal_type in ['weight', 'body_fat', 'strength'] and target_value is None:
            raise ValidationError({
                'target_value': "Target value is required for this goal type."
            })

        return cleaned_data


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'description', 'date_achieved', 'exercise', 'weight', 'reps']
        widgets = {
            'date_achieved': forms.DateInput(attrs={'type': 'date', 'max': timezone.now().date()}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set max date to current date
        self.fields['date_achieved'].widget.attrs['max'] = timezone.now().date().isoformat()


class DateRangeForm(forms.Form):
    """Form for filtering progress by date range"""
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


class MetricsFilterForm(forms.Form):
    """Form for filtering metrics by type"""
    METRIC_CHOICES = (
                         ('all', 'All Metrics'),
                     ) + BodyMetrics.METRIC_TYPES

    metric_type = forms.ChoiceField(
        choices=METRIC_CHOICES,
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
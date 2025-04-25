from django import forms
from .models import WorkoutPlan, PlanExercise, UserPlanExercise, WorkoutSchedule, Exercise, MuscleGroup
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory


class MuscleGroupForm(forms.ModelForm):
    class Meta:
        model = MuscleGroup
        fields = ['name', 'description', 'image']


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = [
            'name', 'description', 'muscle_group', 'secondary_muscle_groups',
            'difficulty', 'category', 'instructions', 'video_url', 'image',
            'equipment_needed', 'is_compound'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'instructions': forms.Textarea(attrs={'rows': 5}),
            'secondary_muscle_groups': forms.CheckboxSelectMultiple(),
        }


class WorkoutPlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ['name', 'description', 'goal', 'intensity', 'duration_weeks', 'is_public']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class PlanExerciseForm(forms.ModelForm):
    class Meta:
        model = PlanExercise
        fields = ['exercise', 'day_of_week', 'order', 'sets', 'reps', 'rest_time', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


# Create a formset for adding multiple exercises to a workout plan
PlanExerciseFormSet = inlineformset_factory(
    WorkoutPlan,
    PlanExercise,
    form=PlanExerciseForm,
    extra=1,
    can_delete=True
)


class UserPlanExerciseForm(forms.ModelForm):
    class Meta:
        model = UserPlanExercise
        fields = ['weight', 'completed_sets', 'completed_reps', 'perceived_difficulty', 'notes', 'completed']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
            'perceived_difficulty': forms.NumberInput(attrs={'min': 1, 'max': 10}),
        }


class WorkoutScheduleForm(forms.ModelForm):
    class Meta:
        model = WorkoutSchedule
        fields = ['workout_plan', 'date', 'start_time', 'end_time', 'day_of_week']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            # Only show workout plans that the user is following
            self.fields['workout_plan'].queryset = WorkoutPlan.objects.filter(
                users__user=self.user,
                users__is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date = cleaned_data.get('date')

        if start_time and end_time and start_time >= end_time:
            raise ValidationError("End time must be after start time.")

        if date and self.user:
            # Check for overlapping workouts on the same day
            overlapping = WorkoutSchedule.objects.filter(
                user=self.user,
                date=date
            )

            if self.instance and self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if start_time and end_time:
                # Check for time overlap
                time_overlap = overlapping.filter(
                    start_time__lt=end_time,
                    end_time__gt=start_time
                )

                if time_overlap.exists():
                    raise ValidationError(
                        "This schedule overlaps with another workout session on the same day."
                    )

        return cleaned_data


class ExerciseFilterForm(forms.Form):
    """Form for filtering exercises"""
    DIFFICULTY_CHOICES = (
                             ('', 'All Difficulties'),
                         ) + Exercise.DIFFICULTY_CHOICES

    CATEGORY_CHOICES = (
                           ('', 'All Categories'),
                       ) + Exercise.CATEGORY_CHOICES

    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Search exercises...',
        'class': 'form-control'
    }))

    muscle_group = forms.ModelChoiceField(
        queryset=MuscleGroup.objects.all(),
        required=False,
        empty_label="All Muscle Groups",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    equipment = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Equipment (e.g. barbell)',
            'class': 'form-control'
        })
    )


class WorkoutPlanFilterForm(forms.Form):
    """Form for filtering workout plans"""
    GOAL_CHOICES = (
                       ('', 'All Goals'),
                   ) + WorkoutPlan.GOAL_CHOICES

    INTENSITY_CHOICES = (
                            ('', 'All Intensities'),
                        ) + WorkoutPlan.INTENSITY_CHOICES

    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Search workout plans...',
        'class': 'form-control'
    }))

    goal = forms.ChoiceField(
        choices=GOAL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    intensity = forms.ChoiceField(
        choices=INTENSITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    duration = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max duration (weeks)',
            'class': 'form-control'
        })
    )
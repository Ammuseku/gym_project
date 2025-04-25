from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.core.exceptions import ValidationError
from django.utils import timezone


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use.")
        return email


class ProfileUpdateForm(forms.ModelForm):
    birthdate = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'max': timezone.now().date()})
    )

    class Meta:
        model = UserProfile
        fields = [
            'avatar', 'gender', 'birthdate', 'height', 'weight',
            'fitness_level', 'primary_goal', 'injuries', 'medical_conditions',
            'weight_unit', 'receive_reminders', 'reminder_time', 'phone_number'
        ]
        widgets = {
            'injuries': forms.Textarea(attrs={'rows': 3}),
            'medical_conditions': forms.Textarea(attrs={'rows': 3}),
            'reminder_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_height(self):
        height = self.cleaned_data.get('height')
        if height is not None and (height < 50 or height > 300):
            raise ValidationError("Please enter a valid height between 50 and 300 cm.")
        return height

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None and (weight < 20 or weight > 500):
            raise ValidationError("Please enter a valid weight between 20 and 500 kg.")
        return weight

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        receive_reminders = self.cleaned_data.get('receive_reminders')

        if receive_reminders and not phone:
            raise ValidationError("Phone number is required for workout reminders.")

        # Simple validation for phone numbers
        if phone and not phone.replace('+', '').isdigit():
            raise ValidationError("Please enter a valid phone number.")

        return phone


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email is already in use.")
        return email
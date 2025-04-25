from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    FITNESS_LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )

    GOAL_CHOICES = (
        ('muscle_gain', 'Muscle Gain'),
        ('fat_loss', 'Fat Loss'),
        ('strength', 'Strength'),
        ('endurance', 'Endurance'),
        ('general_fitness', 'General Fitness'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    height = models.FloatField(help_text="Height in cm", null=True, blank=True)
    weight = models.FloatField(help_text="Weight in kg", null=True, blank=True)
    fitness_level = models.CharField(max_length=20, choices=FITNESS_LEVEL_CHOICES, default='beginner')
    primary_goal = models.CharField(max_length=20, choices=GOAL_CHOICES, default='general_fitness')

    # Health information
    injuries = models.TextField(blank=True, help_text="List any current or previous injuries")
    medical_conditions = models.TextField(blank=True,
                                          help_text="List any medical conditions that might affect training")

    # Preferences
    weight_unit = models.CharField(max_length=3, choices=(('kg', 'Kilograms'), ('lbs', 'Pounds')), default='kg')

    # Notification settings
    receive_reminders = models.BooleanField(default=True)
    reminder_time = models.TimeField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, help_text="For SMS reminders")

    # API integrations
    google_fit_connected = models.BooleanField(default=False)
    apple_health_connected = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def age(self):
        """Calculate age based on birthdate"""
        from datetime import date
        if not self.birthdate:
            return None
        today = date.today()
        return today.year - self.birthdate.year - (
                    (today.month, today.day) < (self.birthdate.month, self.birthdate.day))

    @property
    def bmi(self):
        """Calculate BMI (Body Mass Index)"""
        if not self.height or not self.weight:
            return None
        # Formula: BMI = weight(kg) / height(m)²
        height_in_meters = self.height / 100
        return round(self.weight / (height_in_meters ** 2), 1)

    def get_bmi_category(self):
        """Return BMI category based on calculated BMI"""
        bmi = self.bmi
        if not bmi:
            return None

        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 25:
            return "Normal weight"
        elif 25 <= bmi < 30:
            return "Overweight"
        else:
            return "Obese"

    def save(self, *args, **kwargs):
        # If height or weight changed, update related progress tracking
        if self.pk:
            try:
                old_profile = UserProfile.objects.get(pk=self.pk)

                # Check if weight changed
                if self.weight != old_profile.weight and self.weight is not None:
                    from progress.models import BodyMetrics
                    # Create a new weight record
                    BodyMetrics.objects.create(
                        user=self.user,
                        weight=self.weight,
                        metric_type='weight'
                    )
            except UserProfile.DoesNotExist:
                pass

        super().save(*args, **kwargs)


# Create profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    instance.profile.save()
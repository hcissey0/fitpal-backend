# rest/models.py
from django.db import models
from rest_framework.authtoken.models import Token
from django.conf import settings
from datetime import datetime, time, date

from django.contrib.auth.models import User
from django.dispatch import receiver


# --- Your Existing Profile Model (Slightly Refined) ---
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', on_delete=models.CASCADE)
    # Consolidated weight field
    current_weight = models.FloatField(null=True, blank=True, help_text="Weight in kilograms (kg)")
    height = models.PositiveIntegerField(null=True, blank=True, help_text="Height in centimeters (cm)")
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], null=True, blank=True) # Added gender for better calorie calculation
    # storing main image text in the db
    image = models.TextField(blank=True, null=True, help_text="User's profile image.")
    activity_level = models.CharField(
        max_length=50,
        choices=[
            ('sedentary', 'Sedentary (little or no exercise)'),
            ('lightly_active', 'Lightly Active (light exercise/sports 1-3 days/week)'),
            ('moderately_active', 'Moderately Active (moderate exercise/sports 3-5 days/week)'),
            ('very_active', 'Very Active (hard exercise/sports 6-7 days a week)'),
            ('athlete', 'Intense daily exercise'),
        ],
        null=True, blank=True
    )
    goal = models.CharField(
        max_length=50,
        choices=[
            ('weight_loss', 'Weight Loss'),
            ('maintenance', 'Maintenance'),
            ('muscle_gain', 'Muscle Gain'),
            ('endurance', 'Endurance/Performance'),
        ],
        null=True, blank=True
    )
    # Optional: User can specify dietary preferences or restrictions
    dietary_preferences = models.TextField(blank=True, null=True, help_text="e.g., 'none', 'vegetarian', 'vegan', 'halal', ")

    allergies = models.TextField(blank=True, null=True, help_text="Comma-separated list of allergies")
    disliked_foods = models.TextField(blank=True, null=True, help_text="Comma-separated list of foods you dislike")
    liked_foods = models.TextField(blank=True, null=True, help_text="Comma-separated list of favorite foods")

    disabilities = models.TextField(blank=True, null=True, help_text="Comma-separated list of physical limitations")
    medical_conditions = models.TextField(blank=True, null=True, help_text="E.g., diabetes, hypertension")

    notification_reminders_enabled = models.BooleanField(default=True)
    email_reminders_enabled = models.BooleanField(default=True, help_text="Enable email reminders for workouts and meals.")
    minutes_before_email_reminder = models.PositiveIntegerField(default=30)
    tracking_enabled = models.BooleanField(default=True)
    track_after_rest_timer = models.BooleanField(default=True)
    start_rest_timer_after_exercise = models.BooleanField(default=False, help_text="Start a rest timer after completing an exercise.")

    time_zone = models.CharField(max_length=20, null=True, blank=True, default='UTC')

    breakfast_time = models.TimeField(default=time(8,0))
    lunch_time = models.TimeField(default=time(12,30))
    dinner_time = models.TimeField(default=time(18,0))
    snack_time = models.TimeField(default=time(13,0))

    workout_time = models.TimeField(default=time(6,0))

    connected_to_google_account = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_dietary_preferences_list(self):
        return [d.strip() for d in self.dietary_preferences.split(',') if d.strip()] if self.dietary_preferences else []
    
    def get_allergies_list(self):
        return [a.strip() for a in self.allergies.split(',') if a.strip()] if self.allergies else []
    
    def get_liked_foods_list(self):
        return [f.strip() for f in self.liked_foods.split(',') if f.strip()] if self.liked_foods else []

    def get_disliked_foods_list(self):
        return [f.strip() for f in self.disliked_foods.split(',') if f.strip()] if self.disliked_foods else []

    def get_disabilities_list(self):
        return [d.strip() for d in self.disabilities.split(',') if d.strip()] if self.disabilities else []
    
    def get_medical_conditions_list(self):
        return [m.strip() for m in self.medical_conditions.split(',') if m.strip()] if self.medical_conditions else []
    
    # You can add a property for BMI if you like
    @property
    def bmi(self):
        if self.current_weight and self.height and self.height > 0:
            return round(self.current_weight / ((self.height / 100) ** 2), 2)
        return None

    def __str__(self):
        username = self.user.username or self.user.email or f"User {self.user.id}"
        return f"{username}'s Profile"

# --- New Models for Fitness Plans ---

class FitnessPlan(models.Model):
    """ The main container for a complete plan for a specific period. """
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='fitness_plans')
    start_date = models.DateField()
    end_date = models.DateField()
    workout_added_to_calendar = models.BooleanField(default=False)
    nutrition_added_to_calendar = models.BooleanField(default=False)
    goal_at_creation = models.CharField(null=True, blank=True, max_length=50, help_text="The user's goal when this plan was created.")
    is_active = models.BooleanField(default=True)

    # For debugging and fine-tuning your AI
    ai_prompt_text = models.TextField(blank=True, help_text="The exact prompt sent to the AI.")
    ai_response_raw = models.JSONField(blank=True, null=True, help_text="The raw JSON response from the AI.")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Plan for {self.profile.user.username} from {self.start_date} to {self.end_date}"
    
    class Meta:
        ordering = ['-created_at']


class WorkoutDay(models.Model):
    """ Represents a single day in a workout week. """
    plan = models.ForeignKey(FitnessPlan, on_delete=models.CASCADE, related_name='workout_days')
    DAY_CHOICES = [
        (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'),
        (5, 'Friday'), (6, 'Saturday'), (7, 'Sunday')
    ]
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    title = models.CharField(max_length=100, help_text="e.g., 'Upper Body Strength' or 'Rest Day'")
    description = models.TextField(blank=True, help_text="General instructions for the day's workout.")
    is_rest_day = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['day_of_week']
        unique_together = ['plan', 'day_of_week']

class Exercise(models.Model):
    """ A specific exercise within a WorkoutDay. """
    workout_day = models.ForeignKey(WorkoutDay, on_delete=models.CASCADE, related_name='exercises')
    name = models.CharField(max_length=100, help_text="e.g., 'Push-ups', 'Squats', 'Ampe (Jumping Game)'")
    met_value = models.FloatField(null=True, blank=True, help_text="Metabolic Equivalent of Task value. Represents the intensity of the exercise.")
    duration_mins = models.PositiveIntegerField(help_text="Duration of the exercise in minutes")
    sets = models.PositiveIntegerField()
    reps = models.CharField(max_length=50, help_text="e.g., '10-12', 'AMRAP (As Many Reps As Possible)'")
    rest_period_seconds = models.PositiveIntegerField(help_text="Rest time in seconds between sets.")
    notes = models.TextField(blank=True, null=True, help_text="Specific instructions or Ghanaian context.")

    def __str__(self):
        return f"{self.name} ({self.sets} sets of {self.reps})"


class NutritionDay(models.Model):
    """ Represents a single day's nutrition plan. """
    plan = models.ForeignKey(FitnessPlan, on_delete=models.CASCADE, related_name='nutrition_days')
    day_of_week = models.IntegerField(choices=WorkoutDay.DAY_CHOICES)
    notes = models.TextField(blank=True, null=True, help_text="General advice for the day, e.g., 'Drink 3L of water.'")
    
    # Target macronutrients for the day
    target_calories = models.PositiveIntegerField(null=True, blank=True)
    target_protein_grams = models.PositiveIntegerField(null=True, blank=True)
    target_carbs_grams = models.PositiveIntegerField(null=True, blank=True)
    target_fats_grams = models.PositiveIntegerField(null=True, blank=True)
    target_water_litres = models.FloatField(null=True, blank=True, help_text="Recommended water intake in liters.")
    
    class Meta:
        ordering = ['day_of_week']
        unique_together = ['plan', 'day_of_week']

class Meal(models.Model):
    """ A specific meal within a NutritionDay, focused on Ghanaian cuisine. """
    nutrition_day = models.ForeignKey(NutritionDay, on_delete=models.CASCADE, related_name='meals')
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack')
    ]
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    description = models.CharField(max_length=255, help_text="e.g., 'Waakye with boiled egg and fish'")
    calories = models.PositiveIntegerField()
    protein_grams = models.FloatField()
    carbs_grams = models.FloatField()
    fats_grams = models.FloatField()
    portion_size = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., '1 medium ladle', '2 pieces of chicken'")
    
    def __str__(self):
        return f"{self.get_meal_type_display()}: {self.description}"


class WorkoutTracking(models.Model):
    """ Track completion of individual exercises """
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='tracking_records')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_completed = models.DateField()
    sets_completed = models.PositiveIntegerField(default=0)
    calories_burned = models.PositiveBigIntegerField(default=0)
    notes = models.TextField(blank=True, null=True, help_text="User notes about this workout session")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['exercise', 'user', 'date_completed']
        ordering = ['-date_completed']
    
    def __str__(self):
        return f"{self.user.username} - {self.exercise.name} on {self.date_completed}"

class MealTracking(models.Model):
    """ Track completion of meals """
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='tracking_records')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_completed = models.DateField()
    portion_consumed = models.FloatField(default=1.0, help_text="Portion consumed (1.0 = full portion, 0.5 = half, etc.)")
    notes = models.TextField(blank=True, null=True, help_text="User notes about this meal")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['meal', 'user', 'date_completed']
        ordering = ['-date_completed']
    
    def __str__(self):
        return f"{self.user.username} - {self.meal.description} on {self.date_completed}"
    
class WaterTracking(models.Model):
    """ Track completion of daily water intake """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    nutrition_day = models.ForeignKey(NutritionDay, on_delete=models.CASCADE, related_name='water_tracking_records')
    litres_consumed = models.FloatField(default=0.0, help_text="Litres of water consumed")
    notes = models.TextField(blank=True, null=True, help_text="User notes about this water intake")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # unique_together = ['user', 'date', 'nutrition_day']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.litres_consumed}L on {self.date}"

@receiver(models.signals.post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

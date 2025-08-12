# rest/admin.py
from django.contrib import admin
from rest_framework.authtoken.admin import TokenAdmin
from .models import Profile, FitnessPlan, Meal, Exercise, WorkoutDay, NutritionDay
# Register your models here.

TokenAdmin.raw_id_fields = ('user',)
admin.site.site_header = 'Fitness Planner Admin'
admin.site.register(Profile)  # Register the Profile model
admin.site.register(FitnessPlan)  # Register the FitnessPlan model
admin.site.register(Meal)  # Register the Meal model
admin.site.register(Exercise)  # Register the Exercise model
admin.site.register(WorkoutDay)  # Register the WorkoutDay model
admin.site.register(NutritionDay)  # Register the NutritionDay model
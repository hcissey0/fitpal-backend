# rest/serializers.py

from django.contrib.auth.models import Group
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models import (
    Exercise, FitnessPlan,
    Meal, NutritionDay,
    Profile, WorkoutDay,
    WorkoutTracking, MealTracking,
    WaterTracking,
)
from datetime import date


User = get_user_model()



class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not (email and password):
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        try:
            user = authenticate(email=email, password=password)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        except User.DoesNotExist:
            msg = _('A user with this email does not exist.')
            raise serializers.ValidationError(msg, code='authorization')
        
        attrs['user'] = user
        return attrs

def calculate_calories_burned(met_value, weight, duration_minutes):
    """
    Calculate calories burned based on MET value, weight in kg, and duration in minutes.
    """
    if not all([met_value, weight, duration_minutes]):
        return 0
    return round(((met_value * weight * 3.5) / 200) * duration_minutes)

class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    bmi = serializers.SerializerMethodField()

    # Expose lists as computed fields
    allergies_list = serializers.SerializerMethodField()
    liked_foods_list = serializers.SerializerMethodField()
    disliked_foods_list = serializers.SerializerMethodField()
    disabilities_list = serializers.SerializerMethodField()
    medical_conditions_list = serializers.SerializerMethodField()
    dietary_preferences_list = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'age', 'gender', 'height', 'image', 'current_weight',
            'activity_level', 'goal', 'dietary_preferences',
            'allergies', 'liked_foods', 'disliked_foods',
            'disabilities', 'medical_conditions',
            'allergies_list', 'liked_foods_list', 'disliked_foods_list',
            'disabilities_list', 'medical_conditions_list',
            'bmi', 'created_at', 'updated_at', 'dietary_preferences_list',
            'email_reminders_enabled', 'notification_reminders_enabled',
            'tracking_enabled', 'minutes_before_email_reminder',
            'track_after_rest_timer', 'start_rest_timer_after_exercise',
            'time_zone', 'breakfast_time', 'lunch_time',
            'dinner_time', 'snack_time', 'workout_time',
            'connected_to_google_account', 
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # BMI calculation
    def get_bmi(self, obj):
        if obj.height and obj.current_weight:
            height_m = obj.height / 100 if obj.height > 3 else obj.height
            return round(obj.current_weight / (height_m ** 2), 2)
        return None

    # List conversions
    def get_dietary_preferences_list(self, obj):
        return obj.get_dietary_preferences_list()

    def get_allergies_list(self, obj):
        return obj.get_allergies_list()

    def get_liked_foods_list(self, obj):
        return obj.get_liked_foods_list()

    def get_disliked_foods_list(self, obj):
        return obj.get_disliked_foods_list()

    def get_disabilities_list(self, obj):
        return obj.get_disabilities_list()

    def get_medical_conditions_list(self, obj):
        return obj.get_medical_conditions_list()

class UserSerializer(serializers.ModelSerializer):

    profile = ProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'profile', 'first_name', 'last_name', 'is_active', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
            'email': {'required': True}
            }
        read_only_fields = ['id', 'date_joined', 'is_active']
        
        ordering = ['date_joined']

    def validate_email(self, value):
        """
        Check if the email is already in use.
        """
        # During update, exclude the current user from the check
        if self.instance:
            if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        else:
            # During creation, check all users
            if User.objects.filter(email__iexact=value).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user
    
    def update(self, instance, validated_data):
        # Handle password separately if provided
        password = validated_data.pop('password', None)
        
        # Update the regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Handle password update
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance

class ExerciseSerializer(serializers.ModelSerializer):
    calories_to_burn = serializers.SerializerMethodField()
    class Meta:
        model = Exercise
        fields = '__all__'

    def get_calories_to_burn(self, obj):
        """calculates for calories to be burnt"""
        try:
            weight = obj.workout_day.plan.profile.current_weight
            return calculate_calories_burned(obj.met_value, weight, obj.duration_mins)
        except AttributeError:
            return None

class WorkoutDaySerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = WorkoutDay
        fields = '__all__'

class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = '__all__'

class NutritionDaySerializer(serializers.ModelSerializer):
    meals = MealSerializer(many=True, read_only=True)

    class Meta:
        model = NutritionDay
        fields = '__all__'

class FitnessPlanSerializer(serializers.ModelSerializer):
    workout_days = WorkoutDaySerializer(many=True, read_only=True)
    nutrition_days = NutritionDaySerializer(many=True, read_only=True)
    is_active = serializers.SerializerMethodField()

    def get_is_active(self, obj):
        return obj.start_date <= date.today() <= obj.end_date

    class Meta:
        model = FitnessPlan
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class WorkoutTrackingSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    exercise_sets = serializers.IntegerField(source='exercise.sets', read_only=True)
    
    class Meta:
        model = WorkoutTracking
        fields = ['id', 'exercise', 'exercise_name', 'exercise_sets', 'date_completed', 'sets_completed', 'calories_burned', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']

class MealTrackingSerializer(serializers.ModelSerializer):
    meal_description = serializers.CharField(source='meal.description', read_only=True)
    meal_type = serializers.CharField(source='meal.meal_type', read_only=True)
    
    class Meta:
        model = MealTracking
        fields = ['id', 'meal', 'meal_description', 'meal_type', 'date_completed', 'portion_consumed', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']

class WaterTrackingSerializer(serializers.ModelSerializer):
    target_litres = serializers.FloatField(source='nutrition_day.target_water_litres', read_only=True)
    
    class Meta:
        model = WaterTracking
        fields = ['id', 'date', 'nutrition_day', 'litres_consumed', 'target_litres', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']

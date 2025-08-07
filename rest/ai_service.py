# rest/ai_services.py (or views.py)
from google import genai
from google.genai import types
from os import getenv
from django.conf import settings
from django.db import transaction
from .models import Profile, FitnessPlan, WorkoutDay, Exercise, NutritionDay, Meal
from .schemas import GeneratedPlanSchema # Import your new Pydantic schema
from datetime import date, timedelta
import json

client = genai.Client(api_key=getenv('GOOGLE_AI_API_KEY'))

@transaction.atomic
def generate_and_save_plan_for_user(user_profile: Profile, start_date: date):
    """
    Generates a new fitness and nutrition plan using the Gemini API
    with structured output and saves it to the database.
    """

    print(f"Generating plan for user: {user_profile.user.username}")
    # 1. Construct a detailed prompt from the user's profile
    prompt = f"""
    Generate a comprehensive 7-day fitness and nutrition plan for a user in Ghana.
    The response MUST be a valid JSON object that adheres to the provided schema.

    User Details:
    - Age: {user_profile.age}
    - Gender: {user_profile.gender}
    - Weight: {user_profile.current_weight} kg
    - Height: {user_profile.height} cm
    - Goal: {user_profile.get_goal_display()}
    - Activity Level: {user_profile.get_activity_level_display()}
    - Dietary Preferences: {user_profile.dietary_preferences or 'None specified'}
    - Allergies: {user_profile.allergies or 'None specified'}
    - Liked Foods: {user_profile.liked_foods or 'None specified'}
    - Disliked Foods: {user_profile.disliked_foods or 'None specified'}
    - Disabilities: {user_profile.disabilities or 'None specified'}
    - Medical Conditions: {user_profile.medical_conditions or 'None specified'}
    
    Plan Details:
    - Start Date: {start_date} weekday = {start_date.isoweekday()}

    Instructions:
    - The nutrition plan must focus on common, accessible Ghanaian foods.
    - The workout plan should include exercises that require minimal or no gym equipment.
    - The workouts do not necessarily have to be localized to Ghana.
    - Ensure all fields in the schema are populated accurately. For rest days, the 'exercises' list should be empty.
    - Ensure days and dates matches the provided plan details.
    - Plans are supposed to span up to a maximum of 7 days (weekly, Monday to Sunday).
    """

    # 2. Call the Gemini API with your Pydantic schema
    try:
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # Use the appropriate model
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    )
                ],
                response_mime_type="application/json",
                response_schema=GeneratedPlanSchema,  # Use the Pydantic schema for validation
        )
        )
        
        # The response.text will be a JSON string that is guaranteed to match your Pydantic schema
        plan_data = json.loads(response.text)

    except Exception as e:
        # Handle potential API errors (e.g., content filtering, bad response)
        print(f"Error calling Gemini API: {e}")
        return None

    # 3. Parse the validated data and save it to your Django models
    # The data is already validated by Pydantic via the API!
    
    print(f"Generated plan data: {plan_data}")
    # Create the main FitnessPlan object
    try: 
        new_plan = FitnessPlan.objects.create(
            profile=user_profile,
            start_date=start_date,
            end_date=start_date + timedelta(days=6),
            goal_at_creation=user_profile.goal,
            ai_prompt_text=prompt,
            ai_response_raw=plan_data
        )

        # Create Workout Days and Exercises
        for wd_data in plan_data['workout_days']:
            workout_day = WorkoutDay.objects.create(
                plan=new_plan,
                day_of_week=wd_data['day_of_week'],
                title=wd_data['title'],
                description=wd_data['description'],
                is_rest_day=wd_data['is_rest_day']
            )
            for ex_data in wd_data['exercises']:
                Exercise.objects.create(
                    workout_day=workout_day,
                    name=ex_data['name'],
                    sets=ex_data['sets'],
                    reps=ex_data['reps'],
                    duration_mins=ex_data['duration_mins'],
                    met_value=ex_data['met_value'],
                    rest_period_seconds=ex_data['rest_period_seconds'],
                    notes=ex_data['notes']
                )

        # Create Nutrition Days and Meals
        for nd_data in plan_data['nutrition_days']:
            nutrition_day = NutritionDay.objects.create(
                plan=new_plan,
                day_of_week=nd_data['day_of_week'],
                notes=nd_data['notes'],
                target_calories=nd_data['target_calories'],
                target_protein_grams=nd_data['target_protein_grams'],
                target_carbs_grams=nd_data['target_carbs_grams'],
                target_fats_grams=nd_data['target_fats_grams'],
                target_water_litres=nd_data['target_water_litres'] # Handle optional field
            )
            for meal_data in nd_data['meals']:
                Meal.objects.create(
                    nutrition_day=nutrition_day,
                    meal_type=meal_data['meal_type'],
                    description=meal_data['description'],
                    calories=meal_data['calories'],
                    protein_grams=meal_data['protein_grams'],
                    carbs_grams=meal_data['carbs_grams'],
                    fats_grams=meal_data['fats_grams'],
                    portion_size=meal_data['portion_size']
                )
        print(f"Plan successfully generated and saved for user: {user_profile.user.username}")
        return new_plan
    except Exception as e:
        print(f"Error saving plan to database: {e}")
        return None
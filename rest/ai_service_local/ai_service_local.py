import os
import json
from datetime import date, timedelta
from django.conf import settings
from django.db import transaction
from ..models import Profile, FitnessPlan, WorkoutDay, Exercise, NutritionDay, Meal
from ..schemas import GeneratedPlanSchema

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("Warning: llama-cpp-python not installed. Please install it to use local model inference.")
    print("Install with: pip install llama-cpp-python")


class LocalModel:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
        if LLAMA_CPP_AVAILABLE:
            self.load_model()

    def load_model(self):
        """Load the GGUF model using llama-cpp-python"""
        if not os.path.exists(self.model_path):
            print(f"Model file not found at {self.model_path}")
            print("Please place your DeepSeek_R1_Distill_Qwen_1_5B.gguf model file in the backend directory")
            return
        
        try:
            print(f"Loading model from {self.model_path}")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=4096,  # Context window size
                n_threads=4,  # Number of threads to use
                n_gpu_layers=-1,  # Use GPU if available, -1 for all layers
                verbose=False
            )
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None

    def generate_plan(self, prompt):
        """Generate a fitness plan using the local model"""
        if not self.model:
            print("Model not loaded. Using fallback plan generation.")
            return self._generate_fallback_plan()
        
        try:
            # Create a structured prompt for JSON output
            full_prompt = f"""{prompt}

Please respond with a valid JSON object following this exact structure:
{{
    "workout_days": [
        {{
            "day_of_week": 1,
            "title": "Upper Body Strength",
            "is_rest_day": false,
            "description": "Focus on upper body exercises",
            "exercises": [
                {{
                    "name": "Push-ups",
                    "sets": 3,
                    "reps": "10-15",
                    "rest_period_seconds": 60,
                    "notes": "Keep your body straight"
                }}
            ]
        }}
    ],
    "nutrition_days": [
        {{
            "day_of_week": 1,
            "target_calories": 2000,
            "target_protein_grams": 120,
            "target_carbs_grams": 200,
            "target_fats_grams": 70,
            "notes": "Stay hydrated",
            "meals": [
                {{
                    "meal_type": "breakfast",
                    "description": "Oatmeal with banana",
                    "calories": 400,
                    "protein_grams": 15.0,
                    "carbs_grams": 60.0,
                    "fats_grams": 8.0,
                    "portion_size": "1 bowl"
                }}
            ]
        }}
    ]
}}

JSON Response:"""
            
            # Generate response
            response = self.model(
                full_prompt,
                max_tokens=2048,
                temperature=0.7,
                top_p=0.9,
                echo=False,
                stop=["\n\n", "Human:", "Assistant:"],
            )
            
            response_text = response['choices'][0]['text'].strip()
            
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_text = response_text[json_start:json_end]
                return json_text
            else:
                print("Could not find JSON in model response, using fallback")
                return self._generate_fallback_plan()
                
        except Exception as e:
            print(f"Error generating plan with local model: {e}")
            return self._generate_fallback_plan()

    def _generate_fallback_plan(self):
        """Generate a basic fallback plan when the model fails"""
        fallback_plan = {
            "workout_days": [
                {
                    "day_of_week": 1,
                    "title": "Full Body Workout",
                    "is_rest_day": False,
                    "description": "A comprehensive full-body workout using bodyweight exercises",
                    "exercises": [
                        {
                            "name": "Push-ups",
                            "sets": 3,
                            "reps": "8-12",
                            "rest_period_seconds": 60,
                            "notes": "Keep your core tight and body straight"
                        },
                        {
                            "name": "Squats",
                            "sets": 3,
                            "reps": "12-15",
                            "rest_period_seconds": 60,
                            "notes": "Keep your knees behind your toes"
                        },
                        {
                            "name": "Plank",
                            "sets": 3,
                            "reps": "30-60 seconds",
                            "rest_period_seconds": 60,
                            "notes": "Hold the position steadily"
                        }
                    ]
                },
                {
                    "day_of_week": 2,
                    "title": "Rest Day",
                    "is_rest_day": True,
                    "description": "Active recovery day - light walking or stretching",
                    "exercises": []
                },
                {
                    "day_of_week": 3,
                    "title": "Cardio & Core",
                    "is_rest_day": False,
                    "description": "Cardiovascular exercise and core strengthening",
                    "exercises": [
                        {
                            "name": "Jumping Jacks",
                            "sets": 3,
                            "reps": "20-30",
                            "rest_period_seconds": 45,
                            "notes": "Land softly on your feet"
                        },
                        {
                            "name": "Mountain Climbers",
                            "sets": 3,
                            "reps": "15-20",
                            "rest_period_seconds": 45,
                            "notes": "Keep your core engaged"
                        }
                    ]
                },
                {
                    "day_of_week": 4,
                    "title": "Rest Day",
                    "is_rest_day": True,
                    "description": "Complete rest or gentle stretching",
                    "exercises": []
                },
                {
                    "day_of_week": 5,
                    "title": "Strength Training",
                    "is_rest_day": False,
                    "description": "Focus on building strength with bodyweight exercises",
                    "exercises": [
                        {
                            "name": "Lunges",
                            "sets": 3,
                            "reps": "10-12 each leg",
                            "rest_period_seconds": 60,
                            "notes": "Step forward and lower your back knee"
                        },
                        {
                            "name": "Wall Push-ups",
                            "sets": 3,
                            "reps": "12-15",
                            "rest_period_seconds": 60,
                            "notes": "Great for beginners"
                        }
                    ]
                },
                {
                    "day_of_week": 6,
                    "title": "Active Recovery",
                    "is_rest_day": False,
                    "description": "Light activity and mobility work",
                    "exercises": [
                        {
                            "name": "Walking",
                            "sets": 1,
                            "reps": "20-30 minutes",
                            "rest_period_seconds": 0,
                            "notes": "Maintain a steady, comfortable pace"
                        }
                    ]
                },
                {
                    "day_of_week": 7,
                    "title": "Rest Day",
                    "is_rest_day": True,
                    "description": "Complete rest day",
                    "exercises": []
                }
            ],
            "nutrition_days": [
                {
                    "day_of_week": 1,
                    "target_calories": 2000,
                    "target_protein_grams": 120,
                    "target_carbs_grams": 200,
                    "target_fats_grams": 70,
                    "notes": "Drink plenty of water throughout the day",
                    "meals": [
                        {
                            "meal_type": "breakfast",
                            "description": "Porridge with groundnuts and banana",
                            "calories": 450,
                            "protein_grams": 18.0,
                            "carbs_grams": 65.0,
                            "fats_grams": 12.0,
                            "portion_size": "1 bowl"
                        },
                        {
                            "meal_type": "lunch",
                            "description": "Jollof rice with grilled chicken and vegetables",
                            "calories": 600,
                            "protein_grams": 35.0,
                            "carbs_grams": 70.0,
                            "fats_grams": 18.0,
                            "portion_size": "1 plate"
                        },
                        {
                            "meal_type": "dinner",
                            "description": "Banku with tilapia and okra soup",
                            "calories": 550,
                            "protein_grams": 30.0,
                            "carbs_grams": 45.0,
                            "fats_grams": 20.0,
                            "portion_size": "1 portion"
                        },
                        {
                            "meal_type": "snack",
                            "description": "Roasted plantain with groundnuts",
                            "calories": 200,
                            "protein_grams": 8.0,
                            "carbs_grams": 30.0,
                            "fats_grams": 6.0,
                            "portion_size": "1 medium plantain"
                        }
                    ]
                },
                {
                    "day_of_week": 2,
                    "target_calories": 1900,
                    "target_protein_grams": 110,
                    "target_carbs_grams": 190,
                    "target_fats_grams": 65,
                    "notes": "Focus on hydration and light, nutritious meals",
                    "meals": [
                        {
                            "meal_type": "breakfast",
                            "description": "Kokonte with palm nut soup",
                            "calories": 400,
                            "protein_grams": 15.0,
                            "carbs_grams": 55.0,
                            "fats_grams": 12.0,
                            "portion_size": "1 bowl"
                        },
                        {
                            "meal_type": "lunch",
                            "description": "Waakye with boiled egg and shito",
                            "calories": 520,
                            "protein_grams": 25.0,
                            "carbs_grams": 60.0,
                            "fats_grams": 18.0,
                            "portion_size": "1 plate"
                        },
                        {
                            "meal_type": "dinner",
                            "description": "Kenkey with pepper and fried fish",
                            "calories": 480,
                            "protein_grams": 28.0,
                            "carbs_grams": 40.0,
                            "fats_grams": 20.0,
                            "portion_size": "2 balls kenkey"
                        },
                        {
                            "meal_type": "snack",
                            "description": "Fresh coconut water and meat",
                            "calories": 150,
                            "protein_grams": 3.0,
                            "carbs_grams": 15.0,
                            "fats_grams": 8.0,
                            "portion_size": "1 coconut"
                        }
                    ]
                },
                {
                    "day_of_week": 3,
                    "target_calories": 2100,
                    "target_protein_grams": 125,
                    "target_carbs_grams": 210,
                    "target_fats_grams": 75,
                    "notes": "Higher calorie day to support workout recovery",
                    "meals": [
                        {
                            "meal_type": "breakfast",
                            "description": "Hausa koko with koose",
                            "calories": 420,
                            "protein_grams": 16.0,
                            "carbs_grams": 58.0,
                            "fats_grams": 14.0,
                            "portion_size": "1 bowl with 2 koose"
                        },
                        {
                            "meal_type": "lunch",
                            "description": "Fufu with light soup and chicken",
                            "calories": 650,
                            "protein_grams": 40.0,
                            "carbs_grams": 75.0,
                            "fats_grams": 22.0,
                            "portion_size": "1 portion"
                        },
                        {
                            "meal_type": "dinner",
                            "description": "Fried rice with vegetables and beef",
                            "calories": 580,
                            "protein_grams": 32.0,
                            "carbs_grams": 55.0,
                            "fats_grams": 25.0,
                            "portion_size": "1 plate"
                        },
                        {
                            "meal_type": "snack",
                            "description": "Bofrot with peanut butter",
                            "calories": 250,
                            "protein_grams": 10.0,
                            "carbs_grams": 28.0,
                            "fats_grams": 12.0,
                            "portion_size": "2 pieces"
                        }
                    ]
                },
                {
                    "day_of_week": 4,
                    "target_calories": 1850,
                    "target_protein_grams": 105,
                    "target_carbs_grams": 180,
                    "target_fats_grams": 60,
                    "notes": "Rest day - lighter meals",
                    "meals": [
                        {
                            "meal_type": "breakfast",
                            "description": "Tom brown with milk and honey",
                            "calories": 380,
                            "protein_grams": 14.0,
                            "carbs_grams": 52.0,
                            "fats_grams": 12.0,
                            "portion_size": "1 bowl"
                        },
                        {
                            "meal_type": "lunch",
                            "description": "Yam with kontomire stew",
                            "calories": 500,
                            "protein_grams": 22.0,
                            "carbs_grams": 65.0,
                            "fats_grams": 16.0,
                            "portion_size": "1 portion"
                        },
                        {
                            "meal_type": "dinner",
                            "description": "Gari with beans and palm oil",
                            "calories": 450,
                            "protein_grams": 18.0,
                            "carbs_grams": 55.0,
                            "fats_grams": 15.0,
                            "portion_size": "1 bowl"
                        },
                        {
                            "meal_type": "snack",
                            "description": "Kelewele with groundnuts",
                            "calories": 220,
                            "protein_grams": 8.0,
                            "carbs_grams": 25.0,
                            "fats_grams": 10.0,
                            "portion_size": "1 portion"
                        }
                    ]
                },
                {
                    "day_of_week": 5,
                    "target_calories": 2050,
                    "target_protein_grams": 120,
                    "target_carbs_grams": 205,
                    "target_fats_grams": 72,
                    "notes": "Pre-workout nutrition focus",
                    "meals": [
                        {
                            "meal_type": "breakfast",
                            "description": "Oats with banana and groundnuts",
                            "calories": 440,
                            "protein_grams": 16.0,
                            "carbs_grams": 62.0,
                            "fats_grams": 14.0,
                            "portion_size": "1 bowl"
                        },
                        {
                            "meal_type": "lunch",
                            "description": "Red red with plantain and fish",
                            "calories": 620,
                            "protein_grams": 35.0,
                            "carbs_grams": 68.0,
                            "fats_grams": 20.0,
                            "portion_size": "1 plate"
                        },
                        {
                            "meal_type": "dinner",
                            "description": "Ampesi with nkontomire and eggs",
                            "calories": 520,
                            "protein_grams": 28.0,
                            "carbs_grams": 50.0,
                            "fats_grams": 22.0,
                            "portion_size": "1 portion"
                        },
                        {
                            "meal_type": "snack",
                            "description": "Chin chin with Tiger nuts",
                            "calories": 180,
                            "protein_grams": 6.0,
                            "carbs_grams": 20.0,
                            "fats_grams": 8.0,
                            "portion_size": "1 handful"
                        }
                    ]
                },
                {
                    "day_of_week": 6,
                    "target_calories": 1950,
                    "target_protein_grams": 115,
                    "target_carbs_grams": 195,
                    "target_fats_grams": 65,
                    "notes": "Active recovery day nutrition",
                    "meals": [
                        {
                            "meal_type": "breakfast",
                            "description": "Millet porridge with coconut milk",
                            "calories": 410,
                            "protein_grams": 12.0,
                            "carbs_grams": 58.0,
                            "fats_grams": 15.0,
                            "portion_size": "1 bowl"
                        },
                        {
                            "meal_type": "lunch",
                            "description": "Tuo zaafi with ayoyo soup",
                            "calories": 560,
                            "protein_grams": 28.0,
                            "carbs_grams": 70.0,
                            "fats_grams": 18.0,
                            "portion_size": "1 portion"
                        },
                        {
                            "meal_type": "dinner",
                            "description": "Konkonte with groundnut soup",
                            "calories": 490,
                            "protein_grams": 25.0,
                            "carbs_grams": 45.0,
                            "fats_grams": 20.0,
                            "portion_size": "1 bowl"
                        },
                        {
                            "meal_type": "snack",
                            "description": "Sobolo with meat pie",
                            "calories": 200,
                            "protein_grams": 8.0,
                            "carbs_grams": 22.0,
                            "fats_grams": 8.0,
                            "portion_size": "1 glass + 1 pie"
                        }
                    ]
                },
                {
                    "day_of_week": 7,
                    "target_calories": 1800,
                    "target_protein_grams": 100,
                    "target_carbs_grams": 175,
                    "target_fats_grams": 58,
                    "notes": "Rest day - focus on recovery",
                    "meals": [
                        {
                            "meal_type": "breakfast",
                            "description": "Bread with egg and tea",
                            "calories": 350,
                            "protein_grams": 15.0,
                            "carbs_grams": 45.0,
                            "fats_grams": 12.0,
                            "portion_size": "2 slices + 1 egg"
                        },
                        {
                            "meal_type": "lunch",
                            "description": "Banku with tilapia in tomato sauce",
                            "calories": 540,
                            "protein_grams": 30.0,
                            "carbs_grams": 58.0,
                            "fats_grams": 18.0,
                            "portion_size": "1 portion"
                        },
                        {
                            "meal_type": "dinner",
                            "description": "Jollof rice with chicken and salad",
                            "calories": 480,
                            "protein_grams": 28.0,
                            "carbs_grams": 52.0,
                            "fats_grams": 16.0,
                            "portion_size": "1 plate"
                        },
                        {
                            "meal_type": "snack",
                            "description": "Watermelon and peanuts",
                            "calories": 160,
                            "protein_grams": 7.0,
                            "carbs_grams": 18.0,
                            "fats_grams": 6.0,
                            "portion_size": "1 slice + handful"
                        }
                    ]
                }
            ]
        }
        return json.dumps(fallback_plan)


# Global model instance
_local_model = None

def get_local_model():
    """Get or create the local model instance"""
    global _local_model
    if _local_model is None:
        model_path = os.path.join(settings.BASE_DIR, 'model.gguf')
        _local_model = LocalModel(model_path)
    return _local_model


def generate_and_save_local_plan_for_user(user_profile: Profile):
    """
    Generates a new fitness and nutrition plan using the local model
    and saves it to the database.
    """

    print(f"Generating plan for user: {user_profile.user.username}")

    # Construct a detailed prompt from the user's profile
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

    Instructions:
    - The nutrition plan must focus on common, accessible Ghanaian foods.
    - The workout plan should include exercises that require minimal or no gym equipment.
    - Ensure all fields in the schema are populated accurately. For rest days, the 'exercises' list should be empty.
    """

    # Call the local model
    try:
        local_model = get_local_model()
        response_text = local_model.generate_plan(prompt)
        plan_data = json.loads(response_text)
    except Exception as e:
        print(f"Error calling local model: {e}")
        return None

    # Save to database
    print(f"Generated plan data: {plan_data}")
    try: 
        with transaction.atomic():
            new_plan = FitnessPlan.objects.create(
                profile=user_profile,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=6),
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
                    target_fats_grams=nd_data['target_fats_grams']
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

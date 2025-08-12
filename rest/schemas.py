# rest/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# --- Schemas for AI Generation ---

class ExerciseSchema(BaseModel):
    name: str = Field(..., description="e.g., 'Push-ups', 'Squats', 'Ampe (Jumping Game)'")
    sets: int
    met_value: float = Field(..., description="Metabolic Equivalent of Task value. Represents the intensity of the exercise.")
    duration_mins: int = Field(..., description="Duration of the exercise in minutes")
    reps: str = Field(..., description="e.g., '10-12', 'AMRAP (As Many Reps As Possible)'")
    rest_period_seconds: int = Field(..., description="Rest time in seconds between sets.")
    notes: Optional[str] = Field(None, description="Specific instructions or Ghanaian context.")

class WorkoutDaySchema(BaseModel):
    day_of_week: int = Field(..., ge=1, le=7, description="1 for Monday, 7 for Sunday.")
    title: str = Field(..., description="e.g., 'Upper Body Strength' or 'Rest Day'")
    is_rest_day: bool = False
    description: Optional[str] = Field(None, description="General instructions for the day's workout.")
    exercises: List[ExerciseSchema] = []

class MealSchema(BaseModel):
    meal_type: str = Field(..., description="One of 'breakfast', 'lunch', 'dinner', 'snack'.")
    description: str = Field(..., description="e.g., 'Waakye with boiled egg and fish'")
    calories: int
    protein_grams: float
    carbs_grams: float
    fats_grams: float
    portion_size: Optional[str] = Field(None, description="e.g., '1 medium ladle', '2 pieces of chicken'")

class NutritionDaySchema(BaseModel):
    day_of_week: int = Field(..., ge=1, le=7, description="1 for Monday, 7 for Sunday.")
    target_calories: Optional[int] = None
    target_protein_grams: Optional[int] = None
    target_carbs_grams: Optional[int] = None
    target_fats_grams: Optional[int] = None
    target_water_litres: Optional[float] = Field(None, description="Recommended water intake in liters.")
    notes: Optional[str] = Field(None, description="General advice for the day, e.g., 'Drink 3L of water.'")
    meals: List[MealSchema]

class GeneratedPlanSchema(BaseModel):
    workout_days: List[WorkoutDaySchema]
    nutrition_days: List[NutritionDaySchema]

# --- Schemas for API Input/Output (Validation & Serialization) ---

# --- User and Profile Schemas ---
class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    class Config:
        from_attributes = True

class ProfileIn(BaseModel):
    current_weight: Optional[float] = None
    height: Optional[int] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None
    dietary_preferences: Optional[str] = None
    image: Optional[str] = None

class ProfileOut(ProfileIn):
    id: int
    user: UserSchema
    bmi: Optional[float] = None
    
    class Config:
        from_attributes = True

# --- Plan Generation Schemas ---
class PlanGenerationIn(BaseModel):
    start_date: date
    end_date: date

# --- Detailed Output Schemas (mirroring models for serialization) ---

class ExerciseOut(ExerciseSchema):
    id: int
    class Config:
        from_attributes = True

class MealOut(MealSchema):
    id: int
    class Config:
        from_attributes = True

class WorkoutDayOut(WorkoutDaySchema):
    id: int
    exercises: List[ExerciseOut]
    class Config:
        from_attributes = True

class NutritionDayOut(NutritionDaySchema):
    id: int
    meals: List[MealOut]
    class Config:
        from_attributes = True

class FitnessPlanOut(BaseModel):
    id: int
    start_date: date
    end_date: date
    goal_at_creation: Optional[str] = None
    workout_days: List[WorkoutDayOut]
    nutrition_days: List[NutritionDayOut]

    class Config:
        from_attributes = True

# --- Tracking Schemas ---

class WorkoutTrackingIn(BaseModel):
    exercise: int
    date_completed: date
    sets_completed: int
    notes: Optional[str] = None

class WorkoutTrackingOut(WorkoutTrackingIn):
    id: int
    exercise_name: str
    exercise_sets: int

    class Config:
        from_attributes = True

class MealTrackingIn(BaseModel):
    meal: int
    date_completed: date
    portion_consumed: float
    notes: Optional[str] = None

class MealTrackingOut(MealTrackingIn):
    id: int
    meal_description: str
    meal_type: str

    class Config:
        from_attributes = True

class DailyProgressOut(BaseModel):
    date: date
    day_of_week: int
    workout_progress: float
    nutrition_progress: float
    is_rest_day: bool

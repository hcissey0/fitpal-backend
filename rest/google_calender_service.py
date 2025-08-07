# rest/google_calendar_service.py

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, HttpError
from django.conf import settings
from allauth.socialaccount.models import SocialToken
from datetime import datetime, time, timedelta, date

# --- NEW HELPER FUNCTION ---
def get_or_create_fitpal_calendar(service, calendar_name="FitPal", user_timezone='UTC'):
    """
    Checks if a calendar with the given name exists. If not, it creates one.
    Returns the ID of the calendar.
    """
    try:
        page_token = None
        while True:
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list.get('items', []):
                if calendar_list_entry['summary'] == calendar_name:
                    print(f"Found existing '{calendar_name}' calendar.")
                    return calendar_list_entry['id']
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

        print(f"'{calendar_name}' calendar not found. Creating a new one.")
        calendar_body = {
            'summary': calendar_name,
            'description': 'Fitness and Nutrition Plan from your FitPal app.',
            'timeZone': user_timezone
        }
        created_calendar = service.calendars().insert(body=calendar_body).execute()
        print(f"Created calendar with ID: {created_calendar['id']}")
        return created_calendar['id']
    except HttpError as e:
        print(f"An error occurred: {e}")
        raise Exception(f"Could not get or create the {calendar_name} calendar. Please ensure permissions are correct.")


# --- UPDATED MAIN FUNCTION ---
def create_calendar_events_for_plan(user, fitness_plan, event_type='all'):
    """
    Creates Google Calendar events on a dedicated 'FitPal' calendar
    for a user's fitness plan.
    """
    google_token = SocialToken.objects.filter(account__user=user, account__provider='google').first()
    if not google_token:
        raise Exception("User has not connected their Google account or the token is invalid. Please log in with Google.")

    # Build credentials from stored token
    credentials = Credentials(
        token=google_token.token,
        refresh_token=google_token.token_secret, # allauth stores the refresh token here
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.GOOGLE_AUTH_CLIENT_ID,
        client_secret=settings.GOOGLE_AUTH_CLIENT_SECRET,
        # --- IMPORTANT CHANGE: Scope must be updated to manage calendars ---
        scopes=['https://www.googleapis.com/auth/calendar']
    )

    service = build('calendar', 'v3', credentials=credentials)

    # --- Get or create the dedicated calendar for our app ---
    user_timezone = fitness_plan.profile.time_zone or 'UTC'
    fitpal_calendar_id = get_or_create_fitpal_calendar(service, calendar_name="FitPal", user_timezone=user_timezone)


    success_count = 0
    failure_count = 0
    plan_start_date = fitness_plan.start_date

    # Define reminders based on user profile settings
    reminders_override = []
    if user.profile.email_reminders_enabled:
        reminders_override.append({'method': 'email', 'minutes': user.profile.minutes_before_email_reminder})
    if user.profile.notification_reminders_enabled:
        reminders_override.append({'method': 'popup', 'minutes': 5}) # Defaulting popup to 5 mins

    # --- Create Workout Events ----
    if event_type in ['workout', 'all']:
        workout_days = fitness_plan.workout_days.filter(is_rest_day=False)
        for workout_day in workout_days:
            event_date = plan_start_date + timedelta(days=workout_day.day_of_week - 1)
            
            workout_time = fitness_plan.profile.workout_time
            start_datetime = datetime.combine(event_date, workout_time)
            end_datetime = start_datetime + timedelta(hours=1)
            
            exercise_list = "\n".join([f"- {ex.name} ({ex.sets} sets of {ex.reps})" for ex in workout_day.exercises.all()])
    
            event = {
                'summary': f'💪 Workout: {workout_day.title}',
                'description': f'Your scheduled workout for the day.\n\nExercises:\n{exercise_list}',
                'start': {'dateTime': start_datetime.isoformat(), 'timeZone': user_timezone},
                'end': {'dateTime': end_datetime.isoformat(), 'timeZone': user_timezone},
                'reminders': {
                    'useDefault': False,
                    'overrides': reminders_override
                }
            }
            try:
                # --- CHANGE: Use the new calendar ID ---
                service.events().insert(calendarId=fitpal_calendar_id, body=event).execute()
                success_count += 1
            except Exception as e:
                print(f"Failed to create workout event: {e}")
                failure_count += 1
        
        # This logic is kept as is
        if success_count > 0 and not fitness_plan.workout_added_to_calendar:
            fitness_plan.workout_added_to_calendar = True
            fitness_plan.save()

    # --- Create Nutrition Events ---
    if event_type in ['nutrition', 'all']:
        nutrition_days = fitness_plan.nutrition_days.all()
        for nutrition_day in nutrition_days:
            event_date = plan_start_date + timedelta(days=nutrition_day.day_of_week - 1)
            for meal in nutrition_day.meals.all():
                breakfast_time = fitness_plan.profile.breakfast_time
                lunch_time = fitness_plan.profile.lunch_time
                dinner_time = fitness_plan.profile.dinner_time
                snack_time = fitness_plan.profile.snack_time
                meal_time = {'breakfast': breakfast_time or time(8,0), 'lunch': lunch_time or time(12,30), 'dinner': dinner_time or time(19,0), 'snack': snack_time or time(15,0)}.get(meal.meal_type, time(12,0))
                start_datetime = datetime.combine(event_date, meal_time)
                end_datetime = start_datetime + timedelta(minutes=60)
                
                event = {
                    'summary': f'🥗 {meal.get_meal_type_display()}: {meal.description}',
                    'description': f"Portion: {meal.portion_size}\nCalories: {meal.calories} kcal",
                    'start': {'dateTime': start_datetime.isoformat(), 'timeZone': user_timezone},
                    'end': {'dateTime': end_datetime.isoformat(), 'timeZone': user_timezone},
                    'reminders': {
                        'useDefault': False,
                        'overrides': reminders_override
                    }
                }
                
                try:
                    # --- CHANGE: Use the new calendar ID ---
                    service.events().insert(calendarId=fitpal_calendar_id, body=event).execute()
                    success_count += 1
                except Exception as e:
                    print(f'Failed to create meal event: {e}')
                    failure_count += 1
        
        # This logic is kept as is
        if success_count > 0 and not fitness_plan.nutrition_added_to_calendar:
            fitness_plan.nutrition_added_to_calendar = True
            fitness_plan.save()

    return success_count, failure_count


# # rest/google_calendar_service.py

# from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build
# from django.conf import settings
# from allauth.socialaccount.models import SocialToken
# from datetime import datetime, time, timedelta, date


# def create_calendar_events_for_plan(user, fitness_plan, event_type='all'):
#     """
#     Creates Google Calendar events for a user's fitness plan.
#     """
#     try:
#         # This query should now succeed after running migrations and re-authenticating.
#         google_token = SocialToken.objects.get(account__user=user, account__provider='google')
#     except SocialToken.DoesNotExist:
#         # This error is now a clear indicator of a user who did not use Google to log in.
#         raise Exception("User has not connected their Google account or the token is invalid. Please log in with Google.")

#     # Build credentials from stored token
#     credentials = Credentials(
#         token=google_token.token,
#         refresh_token=google_token.token_secret, # allauth stores the refresh token here
#         token_uri='https://oauth2.googleapis.com/token',
#         # --- FIX: Using the correct variable names from your settings.py ---
#         client_id=settings.GOOGLE_AUTH_CLIENT_ID,
#         client_secret=settings.GOOGLE_AUTH_CLIENT_SECRET,
#         scopes=['https://www.googleapis.com/auth/calendar.events']
#     )

#     service = build('calendar', 'v3', credentials=credentials)
#     success_count = 0
#     failure_count = 0
#     plan_start_date = fitness_plan.start_date

#     reminders_override = []
#     if user.profile.email_reminders_enabled:
#         reminders_override.append({'method': 'email', 'minutes': user.profile.minutes_before_email_reminder})
#     if user.profile.notification_reminders_enabled:
#         reminders_override.append({'method': 'popup', 'minutes': 5})

#     # --- Create Workout Events ----
#     if event_type in ['workout', 'all']:
#         workout_days = fitness_plan.workout_days.filter(is_rest_day=False)
#         for workout_day in workout_days:
#             # --- FIX: Using workout_day.day_of_week, which is an integer ---
#             event_date = plan_start_date + timedelta(days=workout_day.day_of_week - 1)
            
#             workout_time = fitness_plan.profile.workout_time # 5:00 PM
#             start_datetime = datetime.combine(event_date, workout_time)
#             end_datetime = start_datetime + timedelta(hours=1)
            
#             exercise_list = "\n".join([f"- {ex.name} ({ex.sets} sets of {ex.reps})" for ex in workout_day.exercises.all()])
    
#             event = {
#                 'summary': f'💪 Workout: {workout_day.title}',
#                 'description': f'Your scheduled workout for the day.\n\nExercises:\n{exercise_list}',
#                 'start': {'dateTime': start_datetime.isoformat(), 'timeZone': fitness_plan.profile.time_zone or 'UTC'},
#                 'end': {'dateTime': end_datetime.isoformat(), 'timeZone': fitness_plan.profile.time_zone or 'UTC'},
                
#             }
#             try:
#                 service.events().insert(calendarId='primary', body=event).execute()
#                 success_count += 1
#             except Exception as e:
#                 print(f"Failed to create workout event: {e}")
#                 failure_count += 1
#         if success_count > 0:
#             fitness_plan.workout_added_to_calendar = True
#             fitness_plan.save()

#     # --- Create Nutrition Events ---
#     # --- FIX: Corrected typo 'nutrion' to 'nutrition' ---
#     if event_type in ['nutrition', 'all']:
#         nutrition_days = fitness_plan.nutrition_days.all()
#         for nutrition_day in nutrition_days:
#             event_date = plan_start_date + timedelta(days=nutrition_day.day_of_week - 1)
#             for meal in nutrition_day.meals.all():
#                 breakfast_time = fitness_plan.profile.breakfast_time
#                 lunch_time = fitness_plan.profile.lunch_time
#                 dinner_time = fitness_plan.profile.dinner_time
#                 snack_time = fitness_plan.profile.snack_time
#                 meal_time = {'breakfast': breakfast_time or time(8,0), 'lunch': lunch_time or time(12,30), 'dinner': dinner_time or time(19,0), 'snack': snack_time or time(15,0)}.get(meal.meal_type, time(12,0))
#                 start_datetime = datetime.combine(event_date, meal_time)
#                 end_datetime = start_datetime + timedelta(minutes=60)
                
#                 event = {
#                     'summary': f'🥗 {meal.get_meal_type_display()}: {meal.description}',
#                     'description': f"Portion: {meal.portion_size}\nCalories: {meal.calories} kcal",
#                     'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'UTC'},
#                     'end': {'dateTime': end_datetime.isoformat(), 'timeZone': 'UTC'},
#                     'reminders': {
#                         'useDefault': False,
#                         'overrides': reminders_override
#                     }
#                 }
                
#                 try:
#                     service.events().insert(calendarId='primary', body=event).execute()
#                     success_count += 1
#                 except Exception as e:
#                     print(f'Failed to create meal event: {e}')
#                     failure_count += 1
#         if success_count > 0:
#             fitness_plan.nutrition_added_to_calendar = True
#             fitness_plan.save()

#     return success_count, failure_count
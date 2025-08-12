# rest/views.py
import calendar
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import permissions, viewsets, authentication
from rest_framework.decorators import action, authentication_classes
from rest_framework.response import Response

from .ai_service import generate_and_save_plan_for_user
# from ai_local.services import generate_and_save_local_plan_for_user as generate_and_save_plan_for_user
from .serializers import (
    FitnessPlanSerializer, UserSerializer, ProfileSerializer, EmailAuthTokenSerializer,
    WorkoutTrackingSerializer, MealTrackingSerializer, WaterTrackingSerializer
)
from .models import (
 Profile, WorkoutTracking, MealTracking, 
 Exercise, Meal, FitnessPlan, WorkoutDay, NutritionDay,
 WaterTracking,
)
from django.db.models import Count, Q, Sum
from datetime import datetime, date, timedelta
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework import status, generics # Make sure to import status

# google auth imports
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from .google_calender_service import create_calendar_events_for_plan, delete_calendar_events_for_plan, delete_entire_fitpal_calendar
from allauth.socialaccount.models import SocialAccount, SocialToken

from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

class LoginView(generics.GenericAPIView):
    """
    Custom login view that authenticates with email and returns token + user.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = EmailAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        """Handles POST requests to authenticate a user and return a token.
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })

class SignUpView(generics.GenericAPIView):
    """
    Custom signup view that allows user registration and returns token + user.
    """
    queryset = User.objects.all()
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        """Handles POST requests to register a new user and return a token.
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)



class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'me_profile':
            return ProfileSerializer
        return super().get_serializer_class()
    
    
    @action(detail=False, methods=['get', 'patch', 'put'])
    def me(self, request):
        """
        GET: Returns the currently authenticated user.
        PATCH/PUT: Updates the currently authenticated user's details.
        """
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        
        elif request.method in ['PATCH', 'PUT']:
            # Update user details
            serializer = self.get_serializer(
                request.user, 
                data=request.data, 
                partial=True
            )
            print('req', request.data)
            print("got here")
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path='me/delete')
    def me_delete(self, request):
        """
        Deletes the current user, social accounts, and tokens
        """
        user = request.user
        
        try:
            # Delete all social tokens for this user
            social_tokens = SocialToken.objects.filter(account__user=user)
            token_count = social_tokens.count()
            if token_count > 0:
                social_tokens.delete()
                print(f'Deleted {token_count} social token(s)')
            
            # Delete all social accounts for this user  
            social_accounts = SocialAccount.objects.filter(user=user)
            account_count = social_accounts.count()
            if account_count > 0:
                social_accounts.delete()
                print(f'Deleted {account_count} social account(s)')
            
            # Note: Don't delete SocialApp - that's shared across all users
            # SocialApp represents the OAuth app configuration, not user-specific data
            
            # Delete the user (this will cascade delete Profile and other related objects)
            username = user.username
            user.delete()
            print(f'Deleted user: {username}')
            
            return Response({
                'message': 'User account deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            print(f'Error deleting user: {e}')
            return Response({
                'error': 'Failed to delete user account'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
    # @action(detail=False, methods=['delete'], url_path='me/delete')
    # def me_delete(self, request):
    #     """
    #     Deletes the current user
    #     """
    #     user = request.user
    #     socialtoken = SocialAccount.objects.filter(user=user).first()
    #     socialapp = SocialApp.objects.filter(socialtoken=socialtoken).first()
    #     socialtoken.delete() if socialtoken else None
    #     socialapp.delete() if socialapp else None
    #     print('deleted')
    #     user.delete()

    #     return Response({}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get', 'post', 'put', 'patch'], url_path='me/profile')
    def me_profile(self, request):
        """
        Retrieve, create, or update the profile for the currently authenticated user.
        """
        # Try to get the profile, handle if it doesn't exist.
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = None

        if request.method == 'GET':
            if not profile:
                return Response({"detail": "Profile not found. Please create one by sending a POST request."}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)

        elif request.method == 'POST':
            if profile:
                return Response({"detail": "Profile already exists. Use PUT or PATCH to update."}, status=status.HTTP_400_BAD_REQUEST)
            # if SocialAccount.objects.get(user=)
            
            # Use the serializer to validate and create
            serializer = ProfileSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            socialaccount = SocialAccount.objects.filter(user=request.user).first()
            
            # Pass the user in the .save() method, DRF handles the association
            serializer.save(user=request.user, connected_to_google_account=bool(socialaccount))
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method in ['PUT', 'PATCH']:
            if not profile:
                return Response({"detail": "Profile not found. Please create one first."}, status=status.HTTP_404_NOT_FOUND)
            # Use the serializer to validate and update
            # partial=True allows for partial updates with PATCH
            serializer = ProfileSerializer(profile, data=request.data, partial=request.method == 'PATCH')
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=False, methods=['get', 'post', 'delete'], url_path='me/plans')
    def me_plans(self, request):
        """
        GET: Retrieve fitness plans for the authenticated user.
        POST: Generate a new fitness plan for the authenticated user.
        """
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response({"detail": "Profile not found. Please create a profile first."}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            plans = profile.fitness_plans.all()
            
            plans.order_by("created_at")
            serializer = FitnessPlanSerializer(plans, many=True)
            return Response(serializer.data)
        
        if request.method == 'POST':
            start_date_str = request.data.get('start_date')
            print(f'Start date: {start_date_str}')

            if not start_date_str:
                return Response({"detail": "start_date is required."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Use dateutil.parser for robust ISO 8601 parsing
                from dateutil.parser import isoparse
                start_date = isoparse(start_date_str).date()
            except (ValueError, ImportError):
                # Fallback or error for invalid format
                return Response({"detail": "Invalid date format. Use ISO 8601 format."}, status=status.HTTP_400_BAD_REQUEST)
            

            # check if start_date is 7 days less than today
            if (date.today() - start_date).days > 6:
                return Response({"detail": "Cannot create plan for a past date."}, status=status.HTTP_400_BAD_REQUEST)


            # Check for overlapping plans
            overlapping_plans = FitnessPlan.objects.filter(
                profile=profile,
                start_date__lte=start_date,
                end_date__gte=start_date
            )
            if overlapping_plans.exists():
                return Response({"detail": "A plan already exists for the selected date range."}, status=status.HTTP_400_BAD_REQUEST)
            

            # IMPORTANT: This is a long-running task.
            # In production, this should be offloaded to a background worker (e.g., Celery).
            plan = generate_and_save_plan_for_user(profile, start_date)
            if plan:
                serializer = FitnessPlanSerializer(plan)
                return Response({
                    "message": "Fitness plan generated successfully.",
                    "plan": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({"detail": "Failed to generate fitness plan."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        if request.method == 'DELETE':
            # This action is not typically used for listing endpoints, but if needed:
            try:
                print(request.data)
                plan_id = request.data.get('id')
                if not plan_id:
                    return Response({"detail": "Plan ID is required."}, status=status.HTTP_400_BAD_REQUEST)
                plan = FitnessPlan.objects.get(pk=plan_id, profile__user=request.user)
                plan.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except FitnessPlan.DoesNotExist:
                return Response({"detail": "Plan not found."}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'detail': "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get', 'post', 'delete'], url_path='me/workout-tracking')
    def workout_tracking(self, request):
        """
        GET: Retrieve workout tracking records for the authenticated user.
        POST: Create a new workout tracking record.
        DELETE: Delete a workout tracking record.
        """
        if request.method == 'GET':
            date = request.query_params.get('date')
            queryset = WorkoutTracking.objects.filter(user=request.user)
            if date:
                queryset = queryset.filter(date_completed=date)
            queryset = queryset.order_by('-date_completed')
            
            serializer = WorkoutTrackingSerializer(queryset, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            if not request.user.profile.tracking_enabled:
                return Response({'detail': "Tracking is disabled"}, status=status.HTTP_400_BAD_REQUEST)
            data = request.data.copy()
            data['user'] = request.user.id
            serializer = WorkoutTrackingSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not request.user.profile.tracking_enabled:
                return Response({'detail': "Tracking is disabled"}, status=status.HTTP_400_BAD_REQUEST)
            tracking_id = request.data.get('id')
            if not tracking_id:
                return Response({"detail": "Tracking record ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                tracking_record = WorkoutTracking.objects.get(pk=tracking_id, user=request.user)
                tracking_record.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except WorkoutTracking.DoesNotExist:
                return Response({"detail": "Tracking record not found."}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get', 'post', 'delete'], url_path='me/meal-tracking')
    def meal_tracking(self, request):
        """
        GET: Retrieve meal tracking records for the authenticated user.
        POST: Create a new meal tracking record.
        DELETE: Delete a meal tracking record.
        """
        if request.method == 'GET':
            date = request.query_params.get('date')
            queryset = MealTracking.objects.filter(user=request.user)
            if date:
                queryset = queryset.filter(date_completed=date)
            queryset = queryset.order_by('-date_completed')
            
            serializer = MealTrackingSerializer(queryset, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            if not request.user.profile.tracking_enabled:
                return Response({'detail': "Tracking is disabled"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                data = request.data.copy()
                data['user'] = request.user.id
                serializer = MealTrackingSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except:
                return Response({'detail': "Meal already tracked"}, status=status.HTTP_400_BAD_REQUEST)
            
        elif request.method == 'DELETE':
            if not request.user.profile.tracking_enabled:
                return Response({'detail': "Tracking is disabled"}, status=status.HTTP_400_BAD_REQUEST)
            tracking_id = request.data.get('id')
            if not tracking_id:
                return Response({"detail": "Tracking record ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                tracking_record = MealTracking.objects.get(pk=tracking_id, user=request.user)
                tracking_record.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except MealTracking.DoesNotExist:
                return Response({"detail": "Tracking record not found."}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get', 'post', 'delete'], url_path='me/water-tracking')
    def water_tracking(self, request):
        """ Water Tracking handler"""
        
        if request.method == 'GET':
            date = request.query_params.get('date')
            queryset = WaterTracking.objects.filter(user=request.user)
            if date:
                queryset.filter(date=date)
            queryset.order_by('date')

            serializer = WaterTrackingSerializer(queryset, many=True)
            return Response(serializer.data)
        
        elif request.method == "POST":
            if not request.user.profile.tracking_enabled:
                return Response({'detail': "Tracking is disabled"}, status=status.HTTP_400_BAD_REQUEST)
            data = request.data.copy()
            data['user'] = request.user.id
            serializer = WaterTrackingSerializer(data=data)
            print(data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif request.method == 'DELETE':
            if not request.user.profile.tracking_enabled:
                return Response({'detail': "Tracking is disabled"}, status=status.HTTP_400_BAD_REQUEST)
            tracking_id = request.data.get('id')
            if not tracking_id:
                return Response({'detail': "Tracking record ID is required."}, status=status.HTTP_404_NOT_FOUND)
            try:
                tracking_record = WaterTracking.objects.get(pk=tracking_id, user=request.user)
                tracking_record.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except:
                return Response({"detail": "Tracking record not found."}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'], url_path='me/add-plan-to-calendar')
    def add_plan_to_calendar(self, request):
        """ Adds a specified fitness plan to the user's Google Calendar.
        Expects a POST request with:
        {
            "plan_id": <id_of_the_fitness_plan>,
            "type": "all"  // "workout", "nutrition", or "all"
        }"""

        plan_id = request.data.get('plan_id')
        event_type = request.data.get('type', 'all')

        if not plan_id:
            return Response({'detail': "plan_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            plan = FitnessPlan.objects.get(pk=plan_id, profile__user=request.user)
        except FitnessPlan.DoesNotExist:
            return Response({'detail': 'Fitness plan not found or you do not have permission.'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # This is a long running operation
            success_count, failure_count = create_calendar_events_for_plan(request.user, plan, event_type)
            
            if failure_count > 0:
                return Response({
                    'message': f'Partially completed. Added {success_count} events, but {failure_count} failed.',
                    'success_count': success_count,
                    'failure_count': failure_count,
                }, status=status.HTTP_207_MULTI_STATUS)
            return Response({
                'message': f'Successfully added {success_count} events to you Google Calendar.',
                'success_count': success_count,
            })
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['delete'], url_path='me/delete-plan-from-calendar')
    def delete_plan_from_calendar(self, request):
        """ Deletes a specified fitness plan from the user's Google Calendar.
        Expects a DELETE request with:
        {
            "plan_id": <id_of_the_fitness_plan>
        }"""

        plan_id = request.data.get('plan_id')
        event_type = request.data.get('type', 'all')

        if not plan_id:
            return Response({'detail': "plan_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = FitnessPlan.objects.get(pk=plan_id, profile__user=request.user)
        except FitnessPlan.DoesNotExist:
            return Response({'detail': 'Fitness plan not found or you do not have permission.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            # This is a long running operation
            success_count, failure_count = delete_calendar_events_for_plan(request.user, plan, event_type)

            if failure_count > 0:
                return Response({
                    'message': f'Partially completed. Deleted {success_count} events, but {failure_count} failed.',
                    'success_count': success_count,
                    'failure_count': failure_count,
                }, status=status.HTTP_207_MULTI_STATUS)
            return Response({
                'message': f'Successfully deleted {success_count} events from your Google Calendar.',
                'success_count': success_count,
            })
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['delete'], url_path='me/delete-fitpal-calendar')
    def delete_fitpal_calendar(self, request):
        """ Deletes the FitPal calendar for the authenticated user.
        This is a long running operation and should be handled carefully.
        """
        try:
            profile = request.user.profile
            if not profile.fitness_plans.exists():
                return Response({'detail': 'No fitness plans found for this user.'}, status=status.HTTP_404_NOT_FOUND)

            # Delete all calendar events associated with the user's fitness plans
            deleted = delete_entire_fitpal_calendar(request.user)
            if deleted:
                return Response({'detail': 'Successfully deleted the FitPal calendar.'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'detail': 'No FitPal calendar found to delete.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='me/progress')
    def progress(self, request):
        """
        GET: Calculate daily progress for workout and nutrition for a specific date or date range.
        Query params:
        - date: specific date (YYYY-MM-DD)
        - start_date: start of date range (YYYY-MM-DD)
        - end_date: end of date range (YYYY-MM-DD)
        - otherwise: the whole month padded to the full weeks.
        """
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        plans = profile.fitness_plans.all()

        # Parse date parameters
        date_param = request.query_params.get('date')
        start_date_param = request.query_params.get('start_date')
        end_date_param = request.query_params.get('end_date')

        if date_param:
            # Single date
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
                dates = [target_date]
            except ValueError:
                return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        elif start_date_param and end_date_param:
            # Date range
            try:
                start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
                dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
            except ValueError:
                return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Default to the current month, padded to the start and end of the week.
            today = date.today()
            first_day_of_month = today.replace(day=1)
            last_day_of_month_numeric = calendar.monthrange(today.year, today.month)[1]
            last_day_of_month = date(today.year, today.month, last_day_of_month_numeric)

            # Calculate the start date (Monday of the week the month starts in)
            start_date = first_day_of_month - timedelta(days=first_day_of_month.isoweekday() - 1)

            # Calculate the end date (Sunday of the week the month ends in)
            end_date = last_day_of_month + timedelta(days=7 - last_day_of_month.isoweekday())

            dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

        progress_data = []

        for a_plan in plans:
            for target_date in dates:
                if a_plan.start_date <= target_date <= a_plan.end_date:
                    # Calculate day of week (1=Monday, 7=Sunday)
                    day_of_week = target_date.isoweekday()

                    # Get planned workouts for this day
                    workout_day = a_plan.workout_days.filter(day_of_week=day_of_week).first()
                    workout_progress = 0
                    total_exercises = 0
                    if workout_day:
                        total_exercises = workout_day.exercises.count()
                        if not workout_day.is_rest_day:
                            if total_exercises > 0:
                                completed_exercises = WorkoutTracking.objects.filter(
                                    user=request.user,
                                    # date_completed=target_date,
                                    exercise__workout_day=workout_day
                                ).count()
                                workout_progress = (completed_exercises / total_exercises) * 100
                        else:
                            workout_progress = 100  # Rest days are always "complete"

                    # Get planned meals for this day
                    nutrition_day = a_plan.nutrition_days.filter(day_of_week=day_of_week).first()
                    nutrition_progress = 0
                    total_meals = 0
                    water_progress = 0
                    total_water = 0

                    if nutrition_day:
                        total_meals = nutrition_day.meals.count()
                        total_water = nutrition_day.target_water_litres or 0
                        if total_water > 0:
                            completed_water = WaterTracking.objects.filter(
                                user=request.user,
                                nutrition_day=nutrition_day,
                                # date=target_date
                            ).aggregate(total=Sum('litres_consumed'))['total'] or 0.0
                            water_progress = (completed_water / total_water) * 100

                        if total_meals > 0:
                            completed_meals = MealTracking.objects.filter(
                                user=request.user,
                                # date_completed=target_date,
                                meal__nutrition_day=nutrition_day
                            ).count()
                            nutrition_progress = (completed_meals / total_meals) * 100

                    progress_data.append({
                        'date': target_date.strftime('%Y-%m-%d'),
                        'day_of_week': day_of_week,
                        'workout_progress': round(workout_progress, 1),
                        'total_workout': round(total_exercises, 1),
                        'nutrition_progress': round(nutrition_progress, 1),
                        'total_nutrition': round(total_meals, 1),
                        'water_progress': round(water_progress, 1),
                        'total_water': round(total_water, 1),
                        'is_rest_day': workout_day.is_rest_day if workout_day else False
                    })

        return Response({
            'progress': progress_data
        })

# a status view
class StatusView(APIView):
    """
    A simple view to check the status of the API.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        """
        Returns a simple status message.
        """
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    # callback_url = 'http://localhost:3000' # frontend url
    client_class = OAuth2Client

    def get_response(self):
        
        token = self.token
        user = self.user

        return Response({
            'token': token.key if token else None,
            'user': UserSerializer(user).data
        })
    
    
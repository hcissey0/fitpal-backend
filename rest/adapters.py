# rest/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from .models import Profile
from django.utils.text import slugify
from allauth.core.exceptions import ImmediateHttpResponse
from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from allauth.socialaccount.models import SocialAccount

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    
    def pre_social_login(self, request, sociallogin):
        """Handle existing users - connect Google account to existing email"""
        user = sociallogin.user
        if user.id:
            return
        
        try:
            email = sociallogin.account.extra_data.get('email')
            if not email:
                return
            if not sociallogin.account.extra_data.get('verified_email', False):
                return
            
            # Find existing user with same email
            existing_user = User.objects.get(email__iexact=email)
            
            # Populate missing data from Google
            user_data = sociallogin.account.extra_data
            updated = False
            
            if not existing_user.first_name and user_data.get('given_name'):
                existing_user.first_name = user_data.get('given_name')
                updated = True
                
            if not existing_user.last_name and user_data.get('family_name'):
                existing_user.last_name = user_data.get('family_name')
                updated = True
                
            if not existing_user.username:
                base_username = slugify(email.split('@')[0]) or f"user_{existing_user.id}"
                existing_user.username = base_username
                updated = True
            
            if updated:
                existing_user.save()
                print(f"Updated existing user data: {existing_user.email}")
            
            # Connect the Google account
            sociallogin.connect(request, existing_user)
            raise ImmediateHttpResponse(redirect('/'))
            
        except User.DoesNotExist:
            pass  # New user, will be handled in populate_user
    
    def populate_user(self, request, sociallogin, data):
        """Populate user data for new users from Google"""
        user = super().populate_user(request, sociallogin, data)
        
        # Get data from Google
        user_data = sociallogin.account.extra_data
        
        # Populate first name
        if not user.first_name:
            first_name = user_data.get('given_name', '') or user_data.get('first_name', '')
            if first_name:
                user.first_name = first_name
        
        # Populate last name  
        if not user.last_name:
            last_name = user_data.get('family_name', '') or user_data.get('last_name', '')
            if last_name:
                user.last_name = last_name
        
        # Populate email
        if not user.email:
            email = user_data.get('email', '')
            if email:
                user.email = email
        
        # Generate username from email
        if not user.username:
            email = user.email or user_data.get('email', '')
            if email:
                base_username = slugify(email.split('@')[0])
                if base_username:
                    user.username = base_username
                else:
                    user.username = f"google_user_{user_data.get('id', 'unknown')}"
        
        print(f"Populated new user: {user.username}, {user.first_name} {user.last_name}, {user.email}")
        return user

@receiver(user_logged_in)
def user_logged_in_handler(request, user, **kwargs):
    """Handle post-login tasks"""
    try:
        # Create profile if it doesn't exist
        profile, created = Profile.objects.get(user=user)
        
        # Mark as connected to Google if not already
        social = SocialAccount.objects.filter(user=user, provider='google').first()
        if social and not profile.connected_to_google_account:
            profile.connected_to_google_account = True
            profile.save()
            print(f"Marked user {user.username} as connected to Google")
            
    except Exception as e:
        print(f'[Login Hook] Error: {e}')









# # rest/adapters.py
# import email
# from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
# from allauth.account.utils import user_email, user_field
# from django.contrib.auth import get_user_model
# from django.shortcuts import redirect
# from .models import Profile
# from django.utils.text import slugify
# from allauth.core.exceptions import ImmediateHttpResponse
# from django.shortcuts import redirect
# from django.dispatch import receiver
# from allauth.account.signals import user_logged_in
# from allauth.socialaccount.models import SocialApp, SocialAccount

# User = get_user_model()

# class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
#     def new_user(self, request, sociallogin):
#         return super().new_user(request, sociallogin)
    
#     def pre_social_login(self, request, sociallogin):
#         user = sociallogin.user
#         if user.id:
#             return
#         print('presocial is running')
       
#         try:
#             email = sociallogin.account.extra_data.get('email')
#             if not email:
#                 return
#             if not sociallogin.account.extra_data.get('verified_email', False):
#                 return
            
#             # Fix the token app assignment issue
#             if hasattr(sociallogin, "token") and sociallogin.token and not sociallogin.token.app_id:
#                 app = SocialApp.objects.filter(provider=sociallogin.account.provider).first()
#                 if app:
#                     sociallogin.token.app = app
#                     # Save the token to prevent the "unsaved related object" error
#                     try:
#                         sociallogin.token.save()
#                     except Exception as e:
#                         print(f"Error saving token: {e}")
            
#             existing_user = User.objects.get(email__iexact=email)
#             if not existing_user.username:
#                 base_username = slugify(email.split('@')[0]) or f"user_{existing_user.id}"
#                 existing_user.username = base_username
#                 existing_user.save()
#             sociallogin.connect(request, existing_user)
#             raise ImmediateHttpResponse(redirect('/'))
#         except User.DoesNotExist:
#             pass
#         # return super().pre_social_login(request, sociallogin)
    
#     def save_user(self, request, sociallogin, form=None):
#         """
#         Saves a new user instance when a user signs up via a social account.
#         """
#         # Ensure token has proper app assignment before saving
#         if hasattr(sociallogin, "token") and sociallogin.token and not sociallogin.token.app_id:
#             app = SocialApp.objects.filter(provider=sociallogin.account.provider).first()
#             if app:
#                 sociallogin.token.app = app
        
#         user = super().save_user(request, sociallogin, form)
        
#         try:
#             user_data = sociallogin.account.extra_data
#             first_name = user_data.get('given_name', '') or user_data.get('first_name', '')
#             last_name = user_data.get('family_name', '') or user_data.get('last_name', '')
            
#             # Auto-generate username if missing
#             if not user.username:
#                 email = user.email or user_data.get('email', '')
#                 base_username = slugify(email.split('@')[0]) if email else f"user_{user.id}"
#                 user.username = base_username
#                 print('this runs if')
#             print('this runs after if')
            
#             # Populate first and last name if missing
#             if first_name and not user.first_name:
#                 user.first_name = first_name
#             if last_name and not user.last_name:
#                 user.last_name = last_name
            
#             user.save()
#             # Ensure Profile exists
#             # Profile.objects.get_or_create(user=user)
#         except Exception as e:
#             print(f"Error populating user details from social account: {e}")
        
#         return user

# @receiver(user_logged_in)
# def user_logged_in_handler(request, user, **kwargs):
#     try:
#         profile = Profile.objects.get(user=user)
#         social = SocialAccount.objects.filter(user=user, provider='google').first()
#         if social and not profile.connected_to_google_account:
#             profile.connected_to_google_account = True
#             profile.save()
#     except Exception as e:
#         print(f'[Login Hook] Failed to update connected_to_google_account {e}')


# # rest/adapters.py

# import email
# from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
# from allauth.account.utils import user_email, user_field
# from django.contrib.auth import get_user_model
# from django.shortcuts import redirect
# from .models import Profile
# from django.utils.text import slugify
# from allauth.core.exceptions import ImmediateHttpResponse
# from django.shortcuts import redirect
# from django.dispatch import receiver
# from allauth.account.signals import user_logged_in
# from allauth.socialaccount.models import SocialApp, SocialAccount
# User = get_user_model()

# class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

#     def new_user(self, request, sociallogin):
#         return super().new_user(request, sociallogin)


#     def pre_social_login(self, request, sociallogin):
#         user  = sociallogin.user

#         if user.id:
#             return
#         print('presocial is running')
        
#         try:
#             email = sociallogin.account.extra_data.get('email')
#             if not email:
#                 return
#             if not sociallogin.account.extra_data.get('verified_email', False):
#                 return
#             if hasattr(sociallogin, "token") and sociallogin.token and not sociallogin.token.app_id:
#                 app = SocialApp.objects.filter(provider=sociallogin.account.provider).first()
#                 if app:
#                     sociallogin.token.app = app

#             existing_user = User.objects.get(email__iexact=email)
#             if not existing_user.username:
#                 base_username = slugify(email.split('@')[0]) or f"user_{existing_user.id}"
#                 existing_user.username = base_username
#                 existing_user.save()
#             sociallogin.connect(request, existing_user)
#             raise ImmediateHttpResponse(redirect('/'))
#         except User.DoesNotExist:
#             pass
#         # return super().pre_social_login(request, sociallogin)

#     def save_user(self, request, sociallogin, form=None):
#         """
#         Saves a new user instance when a user signs up via a social account.
#         """
#         user = super().save_user(request, sociallogin, form)

#         try:
#             user_data = sociallogin.account.extra_data
#             first_name = user_data.get('given_name', '') or user_data.get('first_name', '')
#             last_name = user_data.get('family_name', '') or user_data.get('last_name', '')

#             # Auto-generate username if missing
#             if not user.username:
#                 email = user.email or user_data.get('email', '')
#                 base_username = slugify(email.split('@')[0]) if email else f"user_{user.id}"
#                 user.username = base_username
#                 print('this rund if')
#             print('this run after if')
#             # Populate first and last name if missing
#             if first_name and not user.first_name:
#                 user.first_name = first_name
#             if last_name and not user.last_name:
#                 user.last_name = last_name

#             user.save()

#             # Ensure Profile exists
#             # Profile.objects.get_or_create(user=user)

#         except Exception as e:
#             print(f"Error populating user details from social account: {e}")

#         return user

# @receiver(user_logged_in)
# def user_logged_in_handler(request, user, **kwargs):
#     try:
#         profile = Profile.objects.get(user=user)

#         social = SocialAccount.objects.filter(user=user, provider='google').first()
#         if social and not profile.connected_to_google_account:
#             profile.connected_to_google_account = True
#             profile.save()
#     except Exception as e:
#         print(f'[Login Hook] Failed to update connected_to_google_account {e}')
    
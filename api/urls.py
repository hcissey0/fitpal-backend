# api/urls.py
"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from rest_framework import routers
from rest import views as rest_views
# from dj_rest_auth.registration.views import SocialAccountListView, SocialAccountDisconnectView

router = routers.DefaultRouter() 
router.register(r'users', rest_views.UserViewSet, basename='user')


urlpatterns = [
    path('admin/', admin.site.urls),
    # auth urls
    path('api/auth/login/', rest_views.LoginView.as_view(), name='auth-login'),
    path('api/auth/signup/', rest_views.SignUpView.as_view(), name='auth-signup'),

    # dj-rest-auth
    path('api/auth/', include('dj_rest_auth.urls')),
    # registration
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

    # google login
    path('api/auth/google/', rest_views.GoogleLogin.as_view(), name='google_login'),

    # see, connect and disconnect social accounts
    # path('api/socialaccounts/', SocialAccountListView.as_view(), name='social_account_list'),
    # path('api/socialaccounts/<int:pk>/disconnect/', SocialAccountDisconnectView.as_view(), nam='social_account_disconnect'),
    
    # allauth urls
    path('accounts/', include('allauth.urls')),

    # other api urls
    path('api/', include(router.urls)),
    path('api/status/', rest_views.StatusView.as_view(), name='status'),
]

from django.urls import path
from . import views

app_name = 'ai_local'

urlpatterns = [
    path('status/', views.model_status, name='model_status'),
    path('test/', views.test_generation, name='test_generation'),
]

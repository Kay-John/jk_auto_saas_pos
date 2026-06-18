from django.urls import path
from . import views

urlpatterns = [
    path('', views.register_screen, name='register_screen'),
]

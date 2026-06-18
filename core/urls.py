from django.urls import path
from . import views

urlpatterns = [
    path('', views.register_screen, name='register_screen'),
    path('process-sale/', views.process_sale, name='process_sale'),
    path('inventory/', views.inventory_dashboard, name='inventory_dashboard'),
    path('inventory/stock-in/', views.stock_intake, name='stock_intake'),
]

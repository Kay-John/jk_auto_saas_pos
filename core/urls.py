from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_screen, name='register_screen'),
    path('process-sale/', views.process_sale, name='process_sale'),
    path('inventory/', views.inventory_dashboard, name='inventory_dashboard'),
    path('inventory/stock-in/', views.stock_intake, name='stock_intake'),
    path('inventory/log-expense/', views.log_expense, name='log_expense'),
]

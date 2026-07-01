from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_screen, name='register_screen'),
    path('pos/', views.pos_screen, name='pos_screen'),
    path('process-sale/', views.process_sale, name='process_sale'),
    path('inventory/', views.inventory_dashboard, name='inventory_dashboard'),
    path('inventory/add-product/', views.add_product, name='add_product'),
    path('inventory/add-supplier/', views.add_supplier, name='add_supplier'),
    path('inventory/import-products/', views.import_products, name='import_products'),
    path('inventory/stock-in/', views.stock_intake, name='stock_intake'),
    path('inventory/log-expense/', views.log_expense, name='log_expense'),
    path('inventory/sales/', views.sales_report, name='sales_report'),
    path('billing/', views.billing_page, name='billing_page'),
]

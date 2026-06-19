import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pos_system.settings")
django.setup()

from core.models import UserProfile, Tenant, Product, ProductUnit

user = UserProfile.objects.get(username="test_cashier")
tenant = user.tenant

p, _ = Product.objects.get_or_create(
    tenant=tenant,
    name="Offline Test Soda",
    barcode="OFFLINE123"
)

ProductUnit.objects.get_or_create(
    product=p,
    unit_name="Bottle",
    retail_price=1.50,
    wholesale_price=1.20
)

print("Test data created for cashier tenant.")

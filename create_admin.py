import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pos_system.settings")
django.setup()

from core.models import UserProfile, Tenant

username = "admin"
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "AdminPass123!")
email = "admin@jk-autopos.com"

# Ensure a default tenant exists for the admin superuser
tenant, created = Tenant.objects.get_or_create(
    name="JK-AutoPOS Admin",
    defaults={'currency': 'USD', 'subscription_status': 'active'}
)

if not UserProfile.objects.filter(username=username).exists():
    print(f"Creating superuser '{username}'...")
    UserProfile.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        role='TENANT_ADMIN',
        tenant=tenant
    )
    print("Superuser created successfully.")
else:
    print(f"Superuser '{username}' already exists. Updating profile context...")
    user = UserProfile.objects.get(username=username)
    user.set_password(password)
    user.role = 'TENANT_ADMIN'
    user.tenant = tenant
    user.save()
    print("Superuser profile updated successfully.")

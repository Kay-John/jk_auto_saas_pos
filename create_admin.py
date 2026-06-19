import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pos_system.settings")
django.setup()

from core.models import UserProfile

username = "admin"
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "AdminPass123!")
email = "admin@jk-autopos.com"

if not UserProfile.objects.filter(username=username).exists():
    print(f"Creating superuser '{username}'...")
    UserProfile.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        role='TENANT_ADMIN' # Assigning a role for application consistency
    )
    print("Superuser created successfully.")
else:
    print(f"Superuser '{username}' already exists. Updating password...")
    user = UserProfile.objects.get(username=username)
    user.set_password(password)
    user.save()
    print("Superuser password updated successfully.")

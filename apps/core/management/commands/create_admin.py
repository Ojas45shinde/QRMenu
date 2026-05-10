import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Creates superuser from environment variables"

    def handle(self, *args, **kwargs):
        username = os.environ.get("DJANGO_ADMIN_USERNAME", "admin")
        password = os.environ.get("DJANGO_ADMIN_PASSWORD", "")
        email    = os.environ.get("DJANGO_ADMIN_EMAIL", "admin@example.com")

        if not password:
            self.stdout.write(self.style.WARNING(
                "DJANGO_ADMIN_PASSWORD not set — skipping superuser creation."
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(
                f'Superuser "{username}" already exists — skipping.'
            ))
            return

        User.objects.create_superuser(username=username, password=password, email=email)
        self.stdout.write(self.style.SUCCESS(
            f'Superuser "{username}" created successfully!'
        ))

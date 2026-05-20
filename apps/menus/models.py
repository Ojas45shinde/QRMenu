from django.db import models
from django.utils import timezone
from datetime import timedelta

from apps.restaurants.models import Restaurant


class MenuCategory(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="categories"
    )
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.restaurant.name} — {self.name}"


class MenuItem(models.Model):
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.CASCADE,
        related_name="items"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to="items/", blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


# ================================
# SUBSCRIPTION MODELS
# ================================

class SubscriptionPlan(models.Model):

    PLAN_CHOICES = (
        ("STANDARD", "Standard"),
        ("PREMIUM", "Premium"),
    )

    name = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        unique=True
    )

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    qr_limit = models.PositiveIntegerField()

    duration_days = models.PositiveIntegerField(default=30)

    def __str__(self):
        return f"{self.name} - ₹{self.price}"


class RestaurantSubscription(models.Model):

    restaurant = models.OneToOneField(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="subscription"
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True
    )

    start_date = models.DateTimeField(
        default=timezone.now
    )

    end_date = models.DateTimeField(
    blank=True,
    null=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        from django.utils import timezone
        return timezone.now().date() > self.end_date
    

    def save(self, *args, **kwargs):

        # Automatically set expiry date
        if not self.end_date and self.plan:
            self.end_date = (
                timezone.now() +
                timedelta(days=self.plan.duration_days)
            )

        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.end_date

    def __str__(self):
        return (
            f"{self.restaurant.name} - "
            f"{self.plan.name}"
        )
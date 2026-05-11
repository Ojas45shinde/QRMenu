from django.db import models
from apps.restaurants.models import Restaurant
from apps.menus.models import MenuItem


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending",    "Pending"),
        ("confirmed",  "Confirmed"),
        ("preparing",  "Preparing"),
        ("ready",      "Ready"),
        ("completed",  "Completed"),
        ("cancelled",  "Cancelled"),
    ]

    restaurant   = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="orders")
    table_number = models.CharField(max_length=50)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    note         = models.TextField(blank=True, help_text="Special instructions from customer")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — {self.restaurant.name} — Table {self.table_number}"

    def calculate_total(self):
        self.total_amount = sum(item.subtotal for item in self.items.all())
        self.save(update_fields=["total_amount"])

    @property
    def status_color(self):
        return {
            "pending":   "yellow",
            "confirmed": "blue",
            "preparing": "orange",
            "ready":     "green",
            "completed": "gray",
            "cancelled": "red",
        }.get(self.status, "gray")


class OrderItem(models.Model):
    order     = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    name      = models.CharField(max_length=200)   # snapshot at time of order
    price     = models.DecimalField(max_digits=8, decimal_places=2)
    quantity  = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.name}"

from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model   = OrderItem
    extra   = 0
    readonly_fields = ["name", "price", "quantity", "subtotal"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display   = ["id", "restaurant", "table_number", "status", "total_amount", "created_at"]
    list_filter    = ["status", "restaurant"]
    search_fields  = ["table_number", "restaurant__name"]
    readonly_fields = ["created_at", "updated_at", "total_amount"]
    inlines        = [OrderItemInline]

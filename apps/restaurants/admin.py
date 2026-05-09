from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Restaurant


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display  = ["name","slug","owner","is_active","created_at"]
    list_filter   = ["is_active"]
    search_fields = ["name","slug","owner__username"]
    prepopulated_fields = {"slug": ("name",)}
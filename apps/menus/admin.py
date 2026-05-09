from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import MenuCategory, MenuItem


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ["name","restaurant","order"]
    inlines      = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display  = ["name","category","price","is_available","is_popular"]
    list_filter   = ["is_available","is_popular"]
    search_fields = ["name"]
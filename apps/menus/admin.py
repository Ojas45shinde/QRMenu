from django.contrib import admin

from .models import (
    MenuCategory,
    MenuItem,
    SubscriptionPlan,
    RestaurantSubscription,
)

# =========================================================
# MENU ITEM INLINE
# =========================================================

class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1


# =========================================================
# MENU CATEGORY ADMIN
# =========================================================

@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "restaurant", "order"]
    list_filter = ["restaurant"]
    search_fields = ["name"]

    inlines = [MenuItemInline]


# =========================================================
# MENU ITEM ADMIN
# =========================================================

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):

    list_display = [
        "name",
        "category",
        "price",
        "is_available",
        "is_popular",
    ]

    list_filter = [
        "is_available",
        "is_popular",
        "category",
    ]

    search_fields = [
        "name",
    ]


# =========================================================
# SUBSCRIPTION PLAN ADMIN
# =========================================================

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):

    list_display = [
        "name",
        "price",
        "duration_days",
        "qr_limit",
        #"is_active",
    ]

    #list_filter = [
    #    "is_active",
    #]

    search_fields = [
        "name",
    ]


# =========================================================
# RESTAURANT SUBSCRIPTION ADMIN
# =========================================================

@admin.register(RestaurantSubscription)
class RestaurantSubscriptionAdmin(admin.ModelAdmin):

    list_display = [
        "restaurant",
        "plan",
        "start_date",
        "end_date",
        "is_active",
    ]

    list_filter = [
        "is_active",
        "plan",
    ]

    search_fields = [
        "restaurant__name",
    ]

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
        "requested_plan",
        "payment_status",
        "start_date",
        "end_date",
        "is_active",
    ]

    list_filter = [
        "is_active",
        "payment_status",
        "plan",
    ]

    search_fields = [
        "restaurant__name",
    ]

    actions = ["activate_subscriptions"]

    @admin.action(description="✓ Mark payment verified & activate selected subscriptions")
    def activate_subscriptions(self, request, queryset):
        activated = 0
        skipped = 0
        for subscription in queryset:
            if subscription.requested_plan or subscription.plan:
                subscription.activate()
                activated += 1
            else:
                skipped += 1
        if activated:
            self.message_user(request, f"Activated {activated} subscription(s).")
        if skipped:
            self.message_user(
                request,
                f"Skipped {skipped} subscription(s) with no plan set.",
                level="warning",
            )

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import MenuCategory, MenuItem
from .forms import MenuCategoryForm, MenuItemForm
from datetime import timedelta
from django.utils import timezone
from apps.restaurants.models import Restaurant
from .models import SubscriptionPlan, RestaurantSubscription


def _get_restaurant(user):
    try:
        return user.restaurant
    except Exception:
        return None

def _has_active_subscription(restaurant):

    try:
        subscription = RestaurantSubscription.objects.get(
            restaurant=restaurant,
            is_active=True
        )

        if subscription.is_expired():
            return False

        return True

    except RestaurantSubscription.DoesNotExist:
        return False


@login_required
def category_list(request):
    restaurant = _get_restaurant(request.user)
    if not restaurant:
        messages.warning(request, "Please set up your restaurant first.")
        return redirect("restaurant_edit")
    cats = MenuCategory.objects.filter(restaurant=restaurant)
    return render(request, "menus/category_list.html", {"categories": cats})


@login_required
def category_create(request):

    restaurant = _get_restaurant(request.user)

    if not restaurant:
        return redirect("restaurant_edit")

    # =====================================
    # SUBSCRIPTION VALIDATION
    # =====================================

    if not _has_active_subscription(restaurant):

        messages.error(
            request,
            "Your subscription is inactive or expired."
        )

        return redirect("subscription_plans")

    # =====================================
    # CREATE CATEGORY
    # =====================================

    form = MenuCategoryForm(request.POST or None)

    if form.is_valid():

        cat = form.save(commit=False)
        cat.restaurant = restaurant
        cat.save()

        messages.success(request, "Category created!")

        return redirect("category_list")

    return render(
        request,
        "menus/category_form.html",
        {"form": form}
    )

@login_required
def category_delete(request, pk):
    restaurant = _get_restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")
    cat = get_object_or_404(MenuCategory, pk=pk, restaurant=restaurant)
    if request.method == "POST":
        cat.delete()
        messages.success(request, "Category deleted.")
        return redirect("category_list")
    return render(request, "menus/confirm_delete.html", {"obj": cat})


@login_required
def item_list(request, cat_pk):
    restaurant = _get_restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")
    cat   = get_object_or_404(MenuCategory, pk=cat_pk, restaurant=restaurant)
    items = cat.items.all().order_by("price")
    return render(request, "menus/item_list.html", {"category": cat, "items": items})


@login_required
def item_create(request, cat_pk):

    restaurant = _get_restaurant(request.user)

    if not restaurant:
        return redirect("restaurant_edit")

    # =====================================
    # SUBSCRIPTION VALIDATION
    # =====================================

    if not _has_active_subscription(restaurant):

        messages.error(
            request,
            "Your subscription is inactive or expired."
        )

        return redirect("subscription_plans")

    # =====================================
    # CREATE ITEM
    # =====================================

    cat = get_object_or_404(
        MenuCategory,
        pk=cat_pk,
        restaurant=restaurant
    )

    form = MenuItemForm(
        request.POST or None,
        request.FILES or None
    )

    if form.is_valid():

        item = form.save(commit=False)
        item.category = cat
        item.save()

        messages.success(request, "Item added!")

        return redirect("item_list", cat_pk=cat.pk)

    return render(
        request,
        "menus/item_form.html",
        {
            "form": form,
            "category": cat
        }
    )


@login_required
def item_edit(request, pk):

    restaurant = _get_restaurant(request.user)

    if not restaurant:
        return redirect("restaurant_edit")

    # =====================================
    # SUBSCRIPTION VALIDATION
    # =====================================

    if not _has_active_subscription(restaurant):

        messages.error(
            request,
            "Your subscription is inactive or expired."
        )

        return redirect("subscription_plans")

    # =====================================
    # EDIT ITEM
    # =====================================

    item = get_object_or_404(
        MenuItem,
        pk=pk,
        category__restaurant=restaurant
    )

    form = MenuItemForm(
        request.POST or None,
        request.FILES or None,
        instance=item
    )

    if form.is_valid():

        form.save()

        messages.success(request, "Item updated!")

        return redirect("item_list", cat_pk=item.category.pk)

    return render(
        request,
        "menus/item_form.html",
        {
            "form": form,
            "category": item.category
        }
    )

@login_required
def item_delete(request, pk):
    restaurant = _get_restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")
    item = get_object_or_404(MenuItem, pk=pk, category__restaurant=restaurant)
    if request.method == "POST":
        cat_pk = item.category.pk
        item.delete()
        messages.success(request, "Item deleted.")
        return redirect("item_list", cat_pk=cat_pk)
    return render(request, "menus/confirm_delete.html", {"obj": item})


# ══════════════════════════════════════════════════════════════
# SUBSCRIPTION VIEWS
# ══════════════════════════════════════════════════════════════

@login_required
def subscription_plans(request):

    plans = SubscriptionPlan.objects.all()

    return render(
        request,
        "subscriptions/plans.html",
        {
            "plans": plans
        }
    )


@login_required
def choose_plan(request, plan_id):

    try:
        restaurant = request.user.restaurant

    except Restaurant.DoesNotExist:

        messages.error(
            request,
            "Please create your restaurant first."
        )

        return redirect("restaurant_edit")

    plan = get_object_or_404(
        SubscriptionPlan,
        id=plan_id
    )

    RestaurantSubscription.objects.update_or_create(

        restaurant=restaurant,

        defaults={

            "plan": plan,

            "start_date": timezone.now(),

            "end_date": timezone.now() + timedelta(days=30),

            "is_active": True
        }
    )

    messages.success(
        request,
        f"{plan.name} plan activated successfully!"
    )

    return redirect("qr_list")

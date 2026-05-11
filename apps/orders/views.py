import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils import timezone
from .models import Order, OrderItem
from apps.restaurants.models import Restaurant
from apps.menus.models import MenuCategory


def _restaurant(user):
    try:
        return user.restaurant
    except Exception:
        return None


# ── Customer: Place Order ────────────────────────────────────────────────────
@require_POST
def place_order(request, restaurant_slug):
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, is_active=True)

    try:
        data         = json.loads(request.body)
        items_data   = data.get("items", [])
        table_number = data.get("table_number", "").strip()
        note         = data.get("note", "").strip()

        if not items_data:
            return JsonResponse({"success": False, "error": "Your cart is empty."}, status=400)

        if not table_number:
            return JsonResponse({"success": False, "error": "Table number is required."}, status=400)

        # Create order
        order = Order.objects.create(
            restaurant=restaurant,
            table_number=table_number,
            note=note,
            status="pending",
        )

        # Add items
        from apps.menus.models import MenuItem
        for item_data in items_data:
            menu_item = MenuItem.objects.filter(pk=item_data.get("id")).first()
            if menu_item and menu_item.is_available:
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    name=menu_item.name,
                    price=menu_item.price,
                    quantity=int(item_data.get("quantity", 1)),
                )

        order.calculate_total()

        return JsonResponse({
            "success":      True,
            "order_id":     order.pk,
            "order_number": f"#{order.pk:04d}",
            "total":        str(order.total_amount),
            "table":        order.table_number,
            "items_count":  order.items.count(),
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ── Waiter: Orders Dashboard ─────────────────────────────────────────────────
@login_required
def orders_dashboard(request):
    restaurant = _restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")

    status_filter = request.GET.get("status", "active")

    if status_filter == "active":
        orders = Order.objects.filter(
            restaurant=restaurant
        ).exclude(status__in=["completed", "cancelled"]).prefetch_related("items")
    elif status_filter == "completed":
        orders = Order.objects.filter(
            restaurant=restaurant,
            status="completed"
        ).prefetch_related("items")[:50]
    else:
        orders = Order.objects.filter(
            restaurant=restaurant
        ).prefetch_related("items")[:100]

    return render(request, "orders/dashboard.html", {
        "orders":        orders,
        "status_filter": status_filter,
        "restaurant":    restaurant,
    })


# ── Waiter: Update Order Status ───────────────────────────────────────────────
@login_required
@require_POST
def update_order_status(request, pk):
    restaurant = _restaurant(request.user)
    order      = get_object_or_404(Order, pk=pk, restaurant=restaurant)
    new_status = request.POST.get("status")

    valid = ["pending", "confirmed", "preparing", "ready", "completed", "cancelled"]
    if new_status in valid:
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Order #{order.pk:04d} marked as {new_status}.")

    # HTMX: return just the order card
    if request.headers.get("HX-Request"):
        return render(request, "orders/partials/order_card.html", {"order": order})

    return redirect("orders_dashboard")


# ── HTMX: Poll for new orders (auto-refresh) ─────────────────────────────────
@login_required
def orders_poll(request):
    """Returns active orders HTML for HTMX polling."""
    restaurant = _restaurant(request.user)
    if not restaurant:
        return JsonResponse({})

    orders = Order.objects.filter(
        restaurant=restaurant
    ).exclude(status__in=["completed", "cancelled"]).prefetch_related("items")

    return render(request, "orders/partials/orders_list.html", {"orders": orders})


# ── Customer: Order Status Check ─────────────────────────────────────────────
def order_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return JsonResponse({
        "status":       order.status,
        "status_label": order.get_status_display(),
        "updated_at":   order.updated_at.strftime("%H:%M"),
    })

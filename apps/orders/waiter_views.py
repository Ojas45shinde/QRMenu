import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Order


def _restaurant(user):
    try:
        return user.restaurant
    except Exception:
        return None


@login_required
def kitchen_screen(request):
    restaurant = _restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")
    active_orders = Order.objects.filter(
        restaurant=restaurant,
        status__in=["pending", "confirmed", "preparing", "ready"],
    ).prefetch_related("items")
    return render(request, "orders/kitchen_screen.html", {
        "restaurant":    restaurant,
        "active_orders": active_orders,
    })


@login_required
@require_POST
def update_status(request, order_id):
    restaurant = _restaurant(request.user)
    if not restaurant:
        return JsonResponse({"error": "No restaurant"}, status=403)
    order = get_object_or_404(Order, pk=order_id, restaurant=restaurant)
    try:
        data       = json.loads(request.body)
        new_status = data.get("status")
    except Exception:
        return JsonResponse({"error": "Invalid request"}, status=400)
    valid = ["pending","confirmed","preparing","ready","completed","cancelled"]
    if new_status not in valid:
        return JsonResponse({"error": "Invalid status"}, status=400)
    order.status = new_status
    order.save(update_fields=["status", "updated_at"])
    return JsonResponse({"success": True, "status": order.status})


@login_required
def orders_json(request):
    restaurant = _restaurant(request.user)
    if not restaurant:
        return JsonResponse({"orders": []})
    orders = Order.objects.filter(
        restaurant=restaurant,
        status__in=["pending","confirmed","preparing","ready"],
    ).prefetch_related("items")
    data = []
    for o in orders:
        data.append({
            "id":         o.pk,
            "table":      o.table_number,
            #"customer":   o.customer_name,
            "status":     o.status,
            "notes":      o.note,
            "total":      float(o.total_amount),
            "item_count": o.items.count(),
            #"item_count": o.get_item_count(),
            "created_at": o.created_at.strftime("%H:%M"),
            "items": [
                {"name": i.name, "qty": i.quantity, "price": float(i.price)}
                for i in o.items.all()
            ],
        })
    return JsonResponse({"orders": data})

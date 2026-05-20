import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from apps.restaurants.models import Restaurant
from apps.menus.models import MenuCategory, MenuItem
from apps.qrcodes.models import QRCode
from .models import Order, OrderItem
from django.db.models import Prefetch
from apps.menus.models import RestaurantSubscription


def place_order(request, restaurant_slug, qr_slug):
    restaurant = get_object_or_404(
        Restaurant, slug=restaurant_slug, is_active=True
    )
    qr = QRCode.objects.filter(
        restaurant=restaurant, slug=qr_slug
    ).first()

    if not qr:
        from django.urls import reverse
        return redirect(
            reverse("public_menu",
                    kwargs={"restaurant_slug": restaurant_slug})
        )

    categories = MenuCategory.objects.filter(
    restaurant=restaurant
).prefetch_related(
    Prefetch(
        'items',
        queryset=MenuItem.objects.order_by('price')
    )
)

    if request.method == "POST":
        # Support both JSON and form POST
        try:
            if request.content_type and "application/json" in request.content_type:
                data = json.loads(request.body)
            else:
                data = json.loads(request.body)
        except Exception:
            return JsonResponse({"error": "Invalid request."}, status=400)

        items_data    = data.get("items", [])
        customer_name = data.get("customer_name", "").strip()
        notes         = data.get("notes", "").strip()

        if not items_data:
            return JsonResponse({"error": "No items selected."}, status=400)

        order = Order.objects.create(
            restaurant    = restaurant,
            table_number  = qr.label,
            
            note          = notes,
            status        = "pending",
        )

        for item_data in items_data:
            try:
                menu_item = MenuItem.objects.get(
                    pk=item_data["id"],
                    category__restaurant=restaurant,
                    is_available=True,
                )
            except (MenuItem.DoesNotExist, KeyError):
                continue
            qty = max(1, int(item_data.get("qty", 1)))
            OrderItem.objects.create(
                order     = order,
                menu_item = menu_item,
                name      = menu_item.name,
                price     = menu_item.price,
                quantity  = qty,
            )
        order.calculate_total()
        
        return JsonResponse({
            "success":  True,
            "order_id": order.pk,
            "total":    float(order.total_amount),
        })

    return render(request, "orders/place_order.html", {
        "restaurant": restaurant,
        "categories": categories,
        "qr":         qr,
    })


def order_confirm(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, "orders/order_confirm.html", {"order": order})

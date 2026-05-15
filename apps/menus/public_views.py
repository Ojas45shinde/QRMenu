import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils import timezone
from apps.restaurants.models import Restaurant
from apps.menus.models import MenuCategory
from apps.qrcodes.models import QRCode


def public_menu(request, restaurant_slug, qr_slug=None):
    restaurant = get_object_or_404(
        Restaurant, slug=restaurant_slug, is_active=True
    )

    if qr_slug:
        qr = QRCode.objects.filter(
            restaurant=restaurant, slug=qr_slug
        ).first()
        if qr:
            qr.scan_count  += 1
            qr.last_scanned = timezone.now()
            qr.save(update_fields=["scan_count", "last_scanned"])
        from django.urls import reverse
        return redirect(
            reverse("place_order",
                    kwargs={"restaurant_slug": restaurant_slug,
                            "qr_slug":         qr_slug})
        )

    # Browse-only (no QR slug)
    if restaurant.use_custom_menu and restaurant.custom_menu_html:
        try:
            fp = restaurant.custom_menu_html.path
            if os.path.exists(fp):
                with open(fp, "r", encoding="utf-8") as f:
                    return HttpResponse(f.read(), content_type="text/html")
        except Exception:
            pass

    categories = MenuCategory.objects.filter(
        restaurant=restaurant
    ).prefetch_related("items")

    return render(request, "menus/public_menu.html", {
        "restaurant": restaurant,
        "categories": categories,
    })

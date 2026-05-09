import os
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.utils import timezone
from apps.restaurants.models import Restaurant
from apps.menus.models import MenuCategory
from apps.qrcodes.models import QRCode


def public_menu(request, restaurant_slug, qr_slug=None):
    # Fetch restaurant
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, is_active=True)

    # Track scan count if accessed via table QR slug
    if qr_slug:
        qr = QRCode.objects.filter(
            restaurant=restaurant, slug=qr_slug
        ).first()
        if qr:
            qr.scan_count += 1
            qr.last_scanned = timezone.now()
            qr.save(update_fields=['scan_count', 'last_scanned'])

    # ── If owner uploaded a custom HTML menu, serve it directly ──
    if restaurant.use_custom_menu and restaurant.custom_menu_html:
        try:
            file_path = restaurant.custom_menu_html.path
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                return HttpResponse(html_content, content_type='text/html')
            else:
                # File missing — fall through to default menu
                pass
        except Exception:
            pass  # Fall through to default menu on any error

    # ── Default: auto-generated Django template menu ──────────────
    categories = MenuCategory.objects.filter(
        restaurant=restaurant
    ).prefetch_related('items')

    return render(request, 'menus/public_menu.html', {
        'restaurant': restaurant,
        'categories': categories,
    })
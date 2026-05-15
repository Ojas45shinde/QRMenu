import os

base = r'C:\Users\acer\Desktop\QRmenu'

# ── 1. Fix QR create view (handles restaurants without owner attr) ────────────
qr_views = '''import io
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import qrcode
from PIL import Image, ImageDraw
from .models import QRCode
from .forms import QRCodeForm
from apps.restaurants.models import Restaurant


def _get_restaurant(user):
    """Safely get restaurant for user, return None if not set up."""
    try:
        return user.restaurant
    except Exception:
        return None


def _make_qr_image(url, size=300):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=3,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = img.resize((size, size), Image.LANCZOS)
    return img


def _template_dark(qr_img, restaurant_name):
    W, H = 600, 900
    canvas = Image.new("RGB", (W, H), "#0D0D0D")
    draw = ImageDraw.Draw(canvas)
    for i in range(4):
        draw.line([(0, 10 + i), (W, 10 + i)], fill="#E63946", width=1)
    draw.text((W//2, 120), "WELCOME TO", fill="#555555", anchor="mm")
    draw.text((W//2, 170), restaurant_name.upper()[:30], fill="#FFFFFF", anchor="mm")
    draw.text((W//2, 210), "Fine Dining Experience", fill="#555555", anchor="mm")
    draw.line([(80, 260), (W-80, 260)], fill="#333333", width=1)
    draw.line([(W//2 - 30, 260), (W//2 + 30, 260)], fill="#E63946", width=2)
    draw.text((W//2, 310), "SCAN TO VIEW OUR MENU", fill="#888888", anchor="mm")
    qr_x = (W - 300) // 2
    qr_y = 340
    draw.rounded_rectangle([qr_x-16, qr_y-16, qr_x+316, qr_y+316], radius=16, fill="#1A1A1A", outline="#E63946", width=3)
    canvas.paste(qr_img, (qr_x, qr_y))
    draw.line([(80, 700), (W-80, 700)], fill="#222222", width=1)
    draw.text((W//2, 730), "NO APP NEEDED - JUST YOUR CAMERA", fill="#444444", anchor="mm")
    draw.text((W//2, 760), "powered by QR Menu", fill="#333333", anchor="mm")
    for i in range(4):
        draw.line([(0, H-10+i), (W, H-10+i)], fill="#E63946", width=1)
    return canvas


def _template_light(qr_img, restaurant_name):
    W, H = 600, 900
    canvas = Image.new("RGB", (W, H), "#FFFDF7")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, W, 180], fill="#FFF0E8")
    draw.text((W//2, 70), "RESTAURANT", fill="#2D1B00", anchor="mm")
    draw.text((W//2, 120), restaurant_name[:30], fill="#2D1B00", anchor="mm")
    draw.text((W//2, 155), "Good food. Good vibes.", fill="#A08060", anchor="mm")
    for i in range(5):
        cx = W//2 - 40 + i*20
        draw.ellipse([cx-3, 198, cx+3, 204], fill="#E8D5C0")
    pill_w, pill_h = 260, 48
    pill_x = (W - pill_w) // 2
    draw.rounded_rectangle([pill_x, 230, pill_x+pill_w, 230+pill_h], radius=pill_h//2, fill="#2D1B00")
    draw.text((W//2, 254), "Scan to view our menu", fill="#FFFFFF", anchor="mm")
    qr_x = (W - 300) // 2
    qr_y = 310
    draw.rounded_rectangle([qr_x-16, qr_y-16, qr_x+316, qr_y+316], radius=16, fill="#FFFFFF", outline="#E8D5C0", width=2)
    canvas.paste(qr_img, (qr_x, qr_y))
    draw.line([(60, 730), (W-60, 730)], fill="#E8D5C0", width=1)
    draw.text((W//2, 760), "No app download needed", fill="#C0A080", anchor="mm")
    draw.text((W//2, 790), "powered by QR Menu", fill="#D0C0B0", anchor="mm")
    return canvas


def _template_bold(qr_img, restaurant_name):
    W, H = 600, 900
    canvas = Image.new("RGB", (W, H), "#E63946")
    draw = ImageDraw.Draw(canvas)
    for y in range(0, H, 40):
        draw.line([(0, y), (W, y)], fill="#D63040", width=1)
    draw.text((W//2, 100), "VIEW",  fill="#FFFFFF", anchor="mm")
    draw.text((W//2, 170), "OUR",   fill="#FFFFFF", anchor="mm")
    draw.text((W//2, 240), "MENU",  fill="#FFFFFF", anchor="mm")
    draw.text((W//2, 290), restaurant_name[:30], fill="#FFCCCC", anchor="mm")
    draw.text((W//2, 350), "v  SCAN HERE  v", fill="#FFB3B3", anchor="mm")
    qr_x = (W - 300) // 2
    qr_y = 380
    draw.rounded_rectangle([qr_x-20, qr_y-20, qr_x+320, qr_y+320], radius=16, fill="#FFFFFF")
    canvas.paste(qr_img, (qr_x, qr_y))
    draw.line([(60, 750), (W-60, 750)], fill="#C02030", width=1)
    draw.text((W//2, 790), "No app needed - Just your camera", fill="#FF9999", anchor="mm")
    draw.text((W//2, 825), "powered by QR Menu", fill="#CC3344", anchor="mm")
    return canvas


TEMPLATES = {
    "dark":  ("Dark Elegant", _template_dark),
    "light": ("Warm Light",   _template_light),
    "bold":  ("Bold Brand",   _template_bold),
}


@login_required
def qr_list(request):
    restaurant = _get_restaurant(request.user)
    if not restaurant:
        messages.warning(request, "Please set up your restaurant first.")
        return redirect("restaurant_edit")
    qrs = QRCode.objects.filter(restaurant=restaurant)
    return render(request, "qrcodes/qr_list.html", {"qrcodes": qrs})


@login_required
def qr_create(request):
    restaurant = _get_restaurant(request.user)
    if not restaurant:
        messages.warning(request, "Please set up your restaurant before adding QR codes.")
        return redirect("restaurant_edit")

    form = QRCodeForm(request.POST or None)
    if form.is_valid():
        # Check for duplicate slug within this restaurant
        from django.utils.text import slugify
        label = form.cleaned_data["label"]
        slug  = slugify(label)
        if QRCode.objects.filter(restaurant=restaurant, slug=slug).exists():
            form.add_error("label", "A QR code with this label already exists. Use a different label.")
        else:
            qr = form.save(commit=False)
            qr.restaurant = restaurant
            qr.save()
            messages.success(request, f"QR code created for {qr.label}!")
            return redirect("qr_list")

    return render(request, "qrcodes/qr_form.html", {"form": form})


@login_required
def qr_download(request, pk):
    restaurant = _get_restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")
    qr = get_object_or_404(QRCode, pk=pk, restaurant=restaurant)
    return render(request, "qrcodes/qr_template_picker.html", {
        "qr": qr,
        "templates": [
            {"key": "dark",  "name": "Dark Elegant", "desc": "Great for fine dining and premium restaurants"},
            {"key": "light", "name": "Warm Light",   "desc": "Perfect for cafes and casual dining"},
            {"key": "bold",  "name": "Bold Brand",   "desc": "High visibility for any restaurant type"},
        ]
    })


@login_required
def qr_download_template(request, pk, template_key):
    restaurant = _get_restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")
    qr = get_object_or_404(QRCode, pk=pk, restaurant=restaurant)

    if template_key not in TEMPLATES:
        messages.error(request, "Invalid template.")
        return redirect("qr_list")

    scan_url     = request.build_absolute_uri(qr.get_scan_url())
    qr_img       = _make_qr_image(scan_url, size=300)
    tpl_name, tpl_fn = TEMPLATES[template_key]
    canvas       = tpl_fn(qr_img, qr.restaurant.name)

    buf = io.BytesIO()
    canvas.save(buf, format="PNG", dpi=(300, 300))
    buf.seek(0)

    response = HttpResponse(buf.getvalue(), content_type="image/png")
    response["Content-Disposition"] = (
        f\'attachment; filename="qr-{qr.restaurant.slug}-{qr.slug}-{template_key}.png"\'
    )
    return response


@login_required
def qr_delete(request, pk):
    restaurant = _get_restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")
    qr = get_object_or_404(QRCode, pk=pk, restaurant=restaurant)
    if request.method == "POST":
        qr.delete()
        messages.success(request, "QR code deleted.")
        return redirect("qr_list")
    return render(request, "qrcodes/confirm_delete.html", {"obj": qr})
'''

# ── 2. Menu views fix (safe restaurant access) ───────────────────────────────
menu_views = '''from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import MenuCategory, MenuItem
from .forms import MenuCategoryForm, MenuItemForm


def _get_restaurant(user):
    try:
        return user.restaurant
    except Exception:
        return None


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
    form = MenuCategoryForm(request.POST or None)
    if form.is_valid():
        cat = form.save(commit=False)
        cat.restaurant = restaurant
        cat.save()
        messages.success(request, "Category created!")
        return redirect("category_list")
    return render(request, "menus/category_form.html", {"form": form})


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
    items = cat.items.all()
    return render(request, "menus/item_list.html", {"category": cat, "items": items})


@login_required
def item_create(request, cat_pk):
    restaurant = _get_restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")
    cat  = get_object_or_404(MenuCategory, pk=cat_pk, restaurant=restaurant)
    form = MenuItemForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        item = form.save(commit=False)
        item.category = cat
        item.save()
        messages.success(request, "Item added!")
        return redirect("item_list", cat_pk=cat.pk)
    return render(request, "menus/item_form.html", {"form": form, "category": cat})


@login_required
def item_edit(request, pk):
    restaurant = _get_restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")
    item = get_object_or_404(MenuItem, pk=pk, category__restaurant=restaurant)
    form = MenuItemForm(request.POST or None, request.FILES or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Item updated!")
        return redirect("item_list", cat_pk=item.category.pk)
    return render(request, "menus/item_form.html", {"form": form, "category": item.category})


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
'''

# ── 3. confirm_delete.html for menus ─────────────────────────────────────────
confirm_delete = """{% extends "base.html" %}
{% block title %}Confirm Delete{% endblock %}
{% block content %}
<div style="max-width:480px;margin:4rem auto;text-align:center;padding:0 1rem;">

  <div style="font-size:3.5rem;margin-bottom:1rem;">🗑️</div>
  <h1 style="font-size:1.6rem;margin-bottom:0.75rem;">Delete "{{ obj }}"?</h1>
  <p style="color:var(--muted);margin-bottom:2rem;line-height:1.6;">
    This action cannot be undone.<br>
    All related data will also be permanently deleted.
  </p>

  <div style="display:flex;gap:1rem;justify-content:center;">
    <form method="POST">
      {% csrf_token %}
      <button type="submit" class="btn btn--danger btn--lg">
        Yes, Delete
      </button>
    </form>
    <a href="javascript:history.back()" class="btn btn--ghost btn--lg">
      Cancel
    </a>
  </div>

</div>
{% endblock %}"""

# ── 4. confirm_delete.html for qrcodes ───────────────────────────────────────
qr_confirm_delete = """{% extends "base.html" %}
{% block title %}Delete QR Code{% endblock %}
{% block content %}
<div style="max-width:480px;margin:4rem auto;text-align:center;padding:0 1rem;">

  <div style="font-size:3.5rem;margin-bottom:1rem;">📱</div>
  <h1 style="font-size:1.6rem;margin-bottom:0.75rem;">Delete "{{ obj }}"?</h1>
  <p style="color:var(--muted);margin-bottom:0.5rem;line-height:1.6;">
    This QR code will stop working immediately.
  </p>
  <p style="color:#DC2626;font-size:0.875rem;margin-bottom:2rem;">
    ⚠ Any printed copies of this QR code will no longer work.
  </p>

  <div style="display:flex;gap:1rem;justify-content:center;">
    <form method="POST">
      {% csrf_token %}
      <button type="submit" class="btn btn--danger btn--lg">
        Yes, Delete
      </button>
    </form>
    <a href="{% url 'qr_list' %}" class="btn btn--ghost btn--lg">
      Cancel
    </a>
  </div>

</div>
{% endblock %}"""

# ── Write all files ───────────────────────────────────────────────────────────
files = {
    r'apps\qrcodes\views.py':                          qr_views,
    r'apps\menus\views.py':                            menu_views,
    r'templates\menus\confirm_delete.html':            confirm_delete,
    r'templates\qrcodes\confirm_delete.html':          qr_confirm_delete,
}

for rel_path, content in files.items():
    full_path = os.path.join(base, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Written: {rel_path}")

print("\nAll files fixed! Now restart the server:")
print("  python manage.py runserver")
print("\nTest these URLs:")
print("  Delete category  -> /menu/categories/<pk>/delete/")
print("  Delete item      -> /menu/items/<pk>/delete/")
print("  Create QR        -> /qr/new/")

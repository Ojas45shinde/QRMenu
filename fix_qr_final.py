import os
import django
import sys

sys.path.insert(0, r'C:\Users\acer\Desktop\QRmenu')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# ── Check current state ───────────────────────────────────────────────────────
from django.contrib.auth.models import User
from apps.restaurants.models import Restaurant
from apps.qrcodes.models import QRCode

print("=" * 60)
print("DIAGNOSIS REPORT")
print("=" * 60)

users = User.objects.all()
print(f"\nTotal users: {users.count()}")

for user in users:
    print(f"\n  User: {user.username}")
    try:
        r = user.restaurant
        print(f"    Restaurant: {r.name} (slug: {r.slug})")
        qrs = QRCode.objects.filter(restaurant=r)
        print(f"    QR Codes: {qrs.count()}")
        for qr in qrs:
            print(f"      - {qr.label} (slug: {qr.slug})")
    except Exception as e:
        print(f"    NO RESTAURANT: {e}")

print("\n" + "=" * 60)
print("FIXING QR CODE SLUG ISSUE")
print("=" * 60)

# Fix: Check for QR codes with empty or duplicate slugs
from django.utils.text import slugify

all_qrs = QRCode.objects.all()
print(f"\nTotal QR codes in DB: {all_qrs.count()}")

for qr in all_qrs:
    if not qr.slug:
        qr.slug = slugify(qr.label) or f"table-{qr.pk}"
        qr.save()
        print(f"  Fixed empty slug for: {qr.label} -> {qr.slug}")
    else:
        print(f"  OK: {qr.label} -> {qr.slug}")

print("\n" + "=" * 60)
print("WRITING FIXED QR VIEWS")
print("=" * 60)

# Write the completely fixed qrcodes/views.py
views_content = r'''import io
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.text import slugify
import qrcode
from PIL import Image, ImageDraw
from .models import QRCode
from .forms import QRCodeForm


def _restaurant(user):
    """Get restaurant for user safely."""
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


def _template_dark(qr_img, name):
    W, H = 600, 900
    c = Image.new("RGB", (W, H), "#0D0D0D")
    d = ImageDraw.Draw(c)
    for i in range(4):
        d.line([(0, 10+i), (W, 10+i)], fill="#E63946", width=1)
    d.text((W//2, 120), "WELCOME TO",        fill="#555555", anchor="mm")
    d.text((W//2, 170), name.upper()[:28],   fill="#FFFFFF", anchor="mm")
    d.text((W//2, 210), "Fine Dining",       fill="#555555", anchor="mm")
    d.line([(80, 260), (W-80, 260)],         fill="#333333", width=1)
    d.line([(W//2-30, 260), (W//2+30, 260)], fill="#E63946", width=2)
    d.text((W//2, 310), "SCAN TO VIEW OUR MENU", fill="#888888", anchor="mm")
    qx, qy = (W-300)//2, 340
    d.rounded_rectangle([qx-16, qy-16, qx+316, qy+316], radius=16, fill="#1A1A1A", outline="#E63946", width=3)
    c.paste(qr_img, (qx, qy))
    d.line([(80, 700), (W-80, 700)],  fill="#222222", width=1)
    d.text((W//2, 730), "NO APP NEEDED", fill="#444444", anchor="mm")
    d.text((W//2, 760), "powered by QR Menu", fill="#333333", anchor="mm")
    for i in range(4):
        d.line([(0, H-10+i), (W, H-10+i)], fill="#E63946", width=1)
    return c


def _template_light(qr_img, name):
    W, H = 600, 900
    c = Image.new("RGB", (W, H), "#FFFDF7")
    d = ImageDraw.Draw(c)
    d.rectangle([0, 0, W, 180], fill="#FFF0E8")
    d.text((W//2, 80),  name[:28],             fill="#2D1B00", anchor="mm")
    d.text((W//2, 120), "Good food. Good vibes.", fill="#A08060", anchor="mm")
    for i in range(5):
        cx = W//2 - 40 + i*20
        d.ellipse([cx-3, 165, cx+3, 171], fill="#E8D5C0")
    pw, ph = 260, 48
    px = (W-pw)//2
    d.rounded_rectangle([px, 195, px+pw, 195+ph], radius=ph//2, fill="#2D1B00")
    d.text((W//2, 219), "Scan to view our menu", fill="#FFFFFF", anchor="mm")
    qx, qy = (W-300)//2, 270
    d.rounded_rectangle([qx-16, qy-16, qx+316, qy+316], radius=16, fill="#FFFFFF", outline="#E8D5C0", width=2)
    c.paste(qr_img, (qx, qy))
    d.line([(60, 650), (W-60, 650)], fill="#E8D5C0", width=1)
    d.text((W//2, 680), "No app download needed", fill="#C0A080", anchor="mm")
    d.text((W//2, 710), "powered by QR Menu",     fill="#D0C0B0", anchor="mm")
    return c


def _template_bold(qr_img, name):
    W, H = 600, 900
    c = Image.new("RGB", (W, H), "#E63946")
    d = ImageDraw.Draw(c)
    for y in range(0, H, 40):
        d.line([(0, y), (W, y)], fill="#D63040", width=1)
    d.text((W//2, 100), "VIEW", fill="#FFFFFF", anchor="mm")
    d.text((W//2, 170), "OUR",  fill="#FFFFFF", anchor="mm")
    d.text((W//2, 240), "MENU", fill="#FFFFFF", anchor="mm")
    d.text((W//2, 285), name[:28],         fill="#FFCCCC", anchor="mm")
    d.text((W//2, 340), "v  SCAN HERE  v", fill="#FFB3B3", anchor="mm")
    qx, qy = (W-300)//2, 370
    d.rounded_rectangle([qx-20, qy-20, qx+320, qy+320], radius=16, fill="#FFFFFF")
    c.paste(qr_img, (qx, qy))
    d.line([(60, 745), (W-60, 745)], fill="#C02030", width=1)
    d.text((W//2, 780), "No app needed - Just your camera", fill="#FF9999", anchor="mm")
    d.text((W//2, 815), "powered by QR Menu",              fill="#CC3344", anchor="mm")
    return c


TEMPLATES = {
    "dark":  ("Dark Elegant", _template_dark),
    "light": ("Warm Light",   _template_light),
    "bold":  ("Bold Brand",   _template_bold),
}


@login_required
def qr_list(request):
    restaurant = _restaurant(request.user)
    if not restaurant:
        messages.warning(request, "Please set up your restaurant first.")
        return redirect("restaurant_edit")
    qrs = QRCode.objects.filter(restaurant=restaurant).order_by("label")
    return render(request, "qrcodes/qr_list.html", {"qrcodes": qrs})


@login_required
def qr_create(request):
    restaurant = _restaurant(request.user)
    if not restaurant:
        messages.warning(request, "Please set up your restaurant before adding QR codes.")
        return redirect("restaurant_edit")

    if request.method == "POST":
        label = request.POST.get("label", "").strip()
        if not label:
            messages.error(request, "Please enter a label for the QR code.")
            return render(request, "qrcodes/qr_form.html", {"label_value": label})

        # Generate unique slug
        base_slug = slugify(label)
        if not base_slug:
            base_slug = f"qr-{QRCode.objects.filter(restaurant=restaurant).count() + 1}"

        # Make slug unique within this restaurant
        slug = base_slug
        counter = 1
        while QRCode.objects.filter(restaurant=restaurant, slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        qr = QRCode.objects.create(
            restaurant=restaurant,
            label=label,
            slug=slug,
        )
        messages.success(request, f'QR code created for "{qr.label}"!')
        return redirect("qr_list")

    return render(request, "qrcodes/qr_form.html", {"label_value": ""})


@login_required
def qr_download(request, pk):
    restaurant = _restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")
    qr = get_object_or_404(QRCode, pk=pk, restaurant=restaurant)
    return render(request, "qrcodes/qr_template_picker.html", {
        "qr": qr,
        "templates": [
            {"key": "dark",  "name": "Dark Elegant", "desc": "Great for fine dining"},
            {"key": "light", "name": "Warm Light",   "desc": "Perfect for cafes"},
            {"key": "bold",  "name": "Bold Brand",   "desc": "High visibility"},
        ]
    })


@login_required
def qr_download_template(request, pk, template_key):
    restaurant = _restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")
    qr = get_object_or_404(QRCode, pk=pk, restaurant=restaurant)

    if template_key not in TEMPLATES:
        messages.error(request, "Invalid template.")
        return redirect("qr_list")

    scan_url      = request.build_absolute_uri(qr.get_scan_url())
    qr_img        = _make_qr_image(scan_url)
    tpl_name, fn  = TEMPLATES[template_key]
    canvas        = fn(qr_img, restaurant.name)

    buf = io.BytesIO()
    canvas.save(buf, format="PNG", dpi=(300, 300))
    buf.seek(0)

    resp = HttpResponse(buf.getvalue(), content_type="image/png")
    resp["Content-Disposition"] = (
        f'attachment; filename="qr-{restaurant.slug}-{qr.slug}-{template_key}.png"'
    )
    return resp


@login_required
def qr_delete(request, pk):
    restaurant = _restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")
    qr = get_object_or_404(QRCode, pk=pk, restaurant=restaurant)
    if request.method == "POST":
        qr.delete()
        messages.success(request, "QR code deleted.")
        return redirect("qr_list")
    return render(request, "qrcodes/confirm_delete.html", {"obj": qr})
'''

views_path = r'C:\Users\acer\Desktop\QRmenu\apps\qrcodes\views.py'
with open(views_path, 'w', encoding='utf-8') as f:
    f.write(views_content)
print(f"✓ Written: apps/qrcodes/views.py")

# Write fixed qr_form.html
qr_form = """{% extends "base.html" %}
{% block title %}New QR Code{% endblock %}
{% block content %}
<div class="page--narrow">

  <div class="breadcrumb">
    <a href="{% url 'dashboard' %}">Dashboard</a>
    <span class="breadcrumb__sep">›</span>
    <a href="{% url 'qr_list' %}">QR Codes</a>
    <span class="breadcrumb__sep">›</span>
    <span class="breadcrumb__current">New QR Code</span>
  </div>

  <div class="card">
    <div class="card__header">
      <h1 style="font-size:1.3rem;">📱 Create New QR Code</h1>
    </div>
    <div class="card__body">

      <div class="alert alert--info mb-3">
        ℹ Give this QR code a label like <strong>Table 1</strong>,
        <strong>Table 2</strong>, <strong>Bar Counter</strong>,
        or <strong>Takeaway</strong>. Each label gets its own unique QR code PNG.
      </div>

      <form method="POST" action="{% url 'qr_create' %}">
        {% csrf_token %}

        <div class="form-group">
          <label class="form-label" for="id_label">
            QR Code Label <span style="color:var(--brand)">*</span>
          </label>
          <input type="text"
                 id="id_label"
                 name="label"
                 class="form-control"
                 placeholder="e.g. Table 1, Table 2, Bar Counter, Takeaway"
                 value="{{ label_value }}"
                 required
                 autofocus>
          <div class="form-help">
            Each label creates a unique QR code. You can create as many as you need.
          </div>
        </div>

        <div style="display:flex;gap:0.75rem;margin-top:1.5rem;">
          <button type="submit" class="btn btn--primary">
            Create QR Code
          </button>
          <a href="{% url 'qr_list' %}" class="btn btn--ghost">Cancel</a>
        </div>

      </form>
    </div>
  </div>

</div>
{% endblock %}"""

qr_form_path = r'C:\Users\acer\Desktop\QRmenu\templates\qrcodes\qr_form.html'
with open(qr_form_path, 'w', encoding='utf-8') as f:
    f.write(qr_form)
print(f"✓ Written: templates/qrcodes/qr_form.html")

# Write confirm_delete for qrcodes
qr_confirm = """{% extends "base.html" %}
{% block title %}Delete QR Code{% endblock %}
{% block content %}
<div style="max-width:480px;margin:4rem auto;text-align:center;padding:0 1rem;">
  <div style="font-size:3.5rem;margin-bottom:1rem;">📱</div>
  <h1 style="font-size:1.6rem;margin-bottom:0.75rem;">Delete "{{ obj }}"?</h1>
  <p style="color:var(--muted);margin-bottom:0.5rem;line-height:1.6;">
    This QR code will stop working immediately.
  </p>
  <p style="color:#DC2626;font-size:0.875rem;margin-bottom:2rem;">
    Any printed copies of this QR code will no longer work.
  </p>
  <div style="display:flex;gap:1rem;justify-content:center;">
    <form method="POST">
      {% csrf_token %}
      <button type="submit" class="btn btn--danger btn--lg">Yes, Delete</button>
    </form>
    <a href="{% url 'qr_list' %}" class="btn btn--ghost btn--lg">Cancel</a>
  </div>
</div>
{% endblock %}"""

qr_del_path = r'C:\Users\acer\Desktop\QRmenu\templates\qrcodes\confirm_delete.html'
with open(qr_del_path, 'w', encoding='utf-8') as f:
    f.write(qr_confirm)
print(f"✓ Written: templates/qrcodes/confirm_delete.html")

# Write confirm_delete for menus
menu_confirm = """{% extends "base.html" %}
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
      <button type="submit" class="btn btn--danger btn--lg">Yes, Delete</button>
    </form>
    <a href="javascript:history.back()" class="btn btn--ghost btn--lg">Cancel</a>
  </div>
</div>
{% endblock %}"""

menu_del_path = r'C:\Users\acer\Desktop\QRmenu\templates\menus\confirm_delete.html'
with open(menu_del_path, 'w', encoding='utf-8') as f:
    f.write(menu_confirm)
print(f"✓ Written: templates/menus/confirm_delete.html")

print("\n" + "=" * 60)
print("ALL DONE! Restart server with:")
print("  python manage.py runserver")
print("\nThen test:")
print("  Create QR -> http://127.0.0.1:8000/qr/new/")
print("  QR list   -> http://127.0.0.1:8000/qr/")
print("=" * 60)

"""
Run from project root:  python redesign_qr.py
Completely redesigns all 3 QR templates + public menu page.
"""
import os, sys, io, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
print("=" * 60)
print("QR Menu — Redesigning QR Templates + Menu")
print("=" * 60)

def write(rel, content):
    path = os.path.join(BASE, rel.replace('/', os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✓ {rel}")

# ══════════════════════════════════════════════════════════════
# 1.  Redesigned QR views with beautiful templates
# ══════════════════════════════════════════════════════════════

qr_views = r'''import io
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.text import slugify
import qrcode
from PIL import Image, ImageDraw, ImageFont
from .models import QRCode
from .forms import QRCodeForm


def _restaurant(user):
    try:
        return user.restaurant
    except Exception:
        return None


def _make_qr(url, size=320, fill="#000000", back="#FFFFFF"):
    """Generate a clean QR code PIL Image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill, back_color=back).convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)
    return img


def _draw_text_centered(draw, text, y, W, fill, size_hint=40):
    """Draw text centered horizontally."""
    # Try to get a default font at an appropriate size
    try:
        from PIL import ImageFont
        # Try loading a bold font — fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", size_hint)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size_hint)
            except:
                font = ImageFont.load_default()
    except:
        font = None

    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, y), text, fill=fill, font=font)
        return bbox[3] - bbox[1]  # height
    else:
        draw.text((W // 2, y), text, fill=fill, anchor="mt")
        return size_hint


# ── TEMPLATE 1: Dark Elegant (Fine Dining) ────────────────────
def _tpl_dark_elegant(qr_img, restaurant_name, table_label):
    W, H = 700, 1050
    img  = Image.new("RGB", (W, H), "#0A0A0A")
    draw = ImageDraw.Draw(img)

    # Gold top border
    draw.rectangle([0, 0, W, 6], fill="#C9A84C")

    # Decorative corner lines - top left
    for i, offset in enumerate([20, 26, 32]):
        draw.line([(offset, 20), (offset+60, 20)], fill="#C9A84C", width=1)
        draw.line([(20, offset), (20, offset+60)], fill="#C9A84C", width=1)
    # top right
    for i, offset in enumerate([20, 26, 32]):
        draw.line([(W-offset-60, 20), (W-offset, 20)], fill="#C9A84C", width=1)
        draw.line([(W-20, offset), (W-20, offset+60)], fill="#C9A84C", width=1)

    # "WELCOME TO" label
    draw.text((W//2, 90), "W E L C O M E  T O", fill="#C9A84C", anchor="mm")

    # Restaurant name — big, white
    name_upper = restaurant_name.upper()[:22]
    draw.text((W//2, 155), name_upper, fill="#FFFFFF", anchor="mm")

    # Thin gold divider
    draw.rectangle([80, 200, W-80, 201], fill="#C9A84C")
    # Small diamond center
    cx, cy = W//2, 200
    draw.polygon([(cx, cy-8), (cx+8, cy), (cx, cy+8), (cx-8, cy)], fill="#C9A84C")

    # "SCAN FOR OUR MENU" text
    draw.text((W//2, 240), "S C A N  F O R  O U R  M E N U", fill="#888888", anchor="mm")

    # QR code with gold border frame
    qr_size = 320
    qr_x    = (W - qr_size) // 2
    qr_y    = 270

    # Outer gold frame
    pad = 18
    draw.rounded_rectangle(
        [qr_x - pad - 4, qr_y - pad - 4,
         qr_x + qr_size + pad + 4, qr_y + qr_size + pad + 4],
        radius=4, fill="#C9A84C"
    )
    # Inner dark frame
    draw.rounded_rectangle(
        [qr_x - pad, qr_y - pad,
         qr_x + qr_size + pad, qr_y + qr_size + pad],
        radius=2, fill="#0A0A0A"
    )
    # White QR background
    draw.rectangle(
        [qr_x, qr_y, qr_x + qr_size, qr_y + qr_size],
        fill="#FFFFFF"
    )
    qr_resized = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    if qr_resized.mode == "RGBA":
        img.paste(qr_resized, (qr_x, qr_y), qr_resized)
    else:
        img.paste(qr_resized, (qr_x, qr_y))

    # Corner decorators on QR frame
    fc = "#C9A84C"
    corners = [
        (qr_x-pad-4, qr_y-pad-4),
        (qr_x+qr_size+pad+4-20, qr_y-pad-4),
        (qr_x-pad-4, qr_y+qr_size+pad+4-20),
        (qr_x+qr_size+pad+4-20, qr_y+qr_size+pad+4-20),
    ]

    # Divider after QR
    y_after = qr_y + qr_size + pad + 4 + 30
    draw.rectangle([80, y_after, W-80, y_after+1], fill="#333333")

    # Table label
    draw.text((W//2, y_after + 35), table_label.upper(), fill="#C9A84C", anchor="mm")

    # "No app needed" footer
    draw.text((W//2, y_after + 80),
              "N O  A P P  N E E D E D  ·  J U S T  S C A N",
              fill="#444444", anchor="mm")

    # Bottom decorative corners
    for i, offset in enumerate([20, 26, 32]):
        draw.line([(offset, H-20), (offset+60, H-20)], fill="#C9A84C", width=1)
        draw.line([(20, H-offset-60), (20, H-offset)], fill="#C9A84C", width=1)
    for i, offset in enumerate([20, 26, 32]):
        draw.line([(W-offset-60, H-20), (W-offset, H-20)], fill="#C9A84C", width=1)
        draw.line([(W-20, H-offset-60), (W-20, H-offset)], fill="#C9A84C", width=1)

    # Gold bottom border
    draw.rectangle([0, H-6, W, H], fill="#C9A84C")

    return img


# ── TEMPLATE 2: Fresh White (Cafe / Casual) ───────────────────
def _tpl_fresh_white(qr_img, restaurant_name, table_label):
    W, H = 700, 1050
    img  = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Top red banner
    draw.rectangle([0, 0, W, 200], fill="#E63946")

    # Decorative circles on banner
    draw.ellipse([-60, -60, 120, 120], outline="#FF6B77", width=3)
    draw.ellipse([-30, -30, 90, 90],   outline="#FF6B77", width=2)
    draw.ellipse([W-120, -60, W+60, 120], outline="#FF6B77", width=3)

    # "SCAN HERE" top
    draw.text((W//2, 60), "SCAN HERE", fill="#FFFFFF", anchor="mm")

    # Restaurant name on banner
    name = restaurant_name[:24].upper()
    draw.text((W//2, 130), name, fill="#FFFFFF", anchor="mm")

    # Red accent stripe
    draw.rectangle([0, 200, W, 212], fill="#C1121F")

    # "FOR OUR" text
    draw.text((W//2, 260), "F O R  O U R", fill="#888888", anchor="mm")

    # Big MENU text
    draw.text((W//2, 320), "MENU", fill="#E63946", anchor="mm")

    # Decorative line
    for x in range(60, W-60, 12):
        draw.rectangle([x, 375, x+7, 377], fill="#E63946")

    # QR code with shadow effect
    qr_size = 300
    qr_x    = (W - qr_size) // 2
    qr_y    = 400

    # Shadow
    draw.rounded_rectangle(
        [qr_x+8, qr_y+8, qr_x+qr_size+8, qr_y+qr_size+8],
        radius=8, fill="#E0E0E0"
    )
    # White card behind QR
    draw.rounded_rectangle(
        [qr_x-20, qr_y-20, qr_x+qr_size+20, qr_y+qr_size+20],
        radius=12, fill="#FFFFFF",
        outline="#EEEEEE", width=2
    )
    qr_resized = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    if qr_resized.mode == "RGBA":
        img.paste(qr_resized, (qr_x, qr_y), qr_resized)
    else:
        img.paste(qr_resized, (qr_x, qr_y))

    # Table badge
    badge_y = qr_y + qr_size + 40
    badge_w = 220
    badge_x = (W - badge_w) // 2
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x+badge_w, badge_y+44],
        radius=22, fill="#E63946"
    )
    draw.text((W//2, badge_y+22), table_label, fill="#FFFFFF", anchor="mm")

    # Footer text
    draw.text((W//2, badge_y+80),
              "Open your camera & point at the QR code",
              fill="#AAAAAA", anchor="mm")
    draw.text((W//2, badge_y+110),
              "No app download required",
              fill="#CCCCCC", anchor="mm")

    # Bottom red strip
    draw.rectangle([0, H-50, W, H], fill="#E63946")
    draw.text((W//2, H-25), "Powered by QR Menu", fill="rgba(255,255,255,128)", anchor="mm")

    return img


# ── TEMPLATE 3: Bold Street (Modern / Fast food) ──────────────
def _tpl_bold_street(qr_img, restaurant_name, table_label):
    W, H = 700, 1050
    img  = Image.new("RGB", (W, H), "#1A1A1A")
    draw = ImageDraw.Draw(img)

    # Diagonal yellow accent block
    draw.polygon([(0,0),(W,0),(W,320),(0,200)], fill="#FFB703")

    # Black overlay text area on yellow
    draw.rectangle([0, 0, W, 40], fill="#1A1A1A")

    # Restaurant name - big and bold on yellow
    draw.text((W//2, 100), "VIEW OUR", fill="#1A1A1A", anchor="mm")
    draw.text((W//2, 180), "MENU", fill="#1A1A1A", anchor="mm")

    # Restaurant name smaller below
    draw.text((W//2, 250), restaurant_name[:28], fill="#1A1A1A", anchor="mm")

    # Dark section
    dark_y = 310

    # "SCAN HERE" with arrows
    draw.text((W//2 - 80, dark_y + 50), "▼", fill="#FFB703", anchor="mm")
    draw.text((W//2, dark_y + 50), "SCAN HERE", fill="#FFFFFF", anchor="mm")
    draw.text((W//2 + 80, dark_y + 50), "▼", fill="#FFB703", anchor="mm")

    # QR code - large, centered
    qr_size = 320
    qr_x    = (W - qr_size) // 2
    qr_y    = dark_y + 80

    # Yellow glow behind QR
    draw.rounded_rectangle(
        [qr_x-12, qr_y-12, qr_x+qr_size+12, qr_y+qr_size+12],
        radius=8, fill="#FFB703"
    )
    # White QR background
    draw.rectangle(
        [qr_x, qr_y, qr_x+qr_size, qr_y+qr_size],
        fill="#FFFFFF"
    )
    qr_resized = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    if qr_resized.mode == "RGBA":
        img.paste(qr_resized, (qr_x, qr_y), qr_resized)
    else:
        img.paste(qr_resized, (qr_x, qr_y))

    # Table label - yellow pill
    tl_y = qr_y + qr_size + 30
    draw.rounded_rectangle(
        [(W-240)//2, tl_y, (W+240)//2, tl_y+50],
        radius=25, fill="#FFB703"
    )
    draw.text((W//2, tl_y+25), table_label.upper(), fill="#1A1A1A", anchor="mm")

    # Bottom info
    draw.text((W//2, tl_y+80),
              "No app · Just scan · Instant menu",
              fill="#555555", anchor="mm")

    # Yellow bottom bar
    draw.rectangle([0, H-45, W, H], fill="#FFB703")
    draw.text((W//2, H-22), restaurant_name[:30], fill="#1A1A1A", anchor="mm")

    return img


TEMPLATES = {
    "dark":   ("Dark Elegant",  _tpl_dark_elegant),
    "white":  ("Fresh White",   _tpl_fresh_white),
    "bold":   ("Bold Street",   _tpl_bold_street),
}


@login_required
def qr_list(request):
    restaurant = _restaurant(request.user)
    if not restaurant:
        from django.contrib import messages
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
            messages.error(request, "Please enter a label.")
            return render(request, "qrcodes/qr_form.html", {"label_value": ""})

        base_slug = slugify(label) or f"qr-{QRCode.objects.filter(restaurant=restaurant).count()+1}"
        slug, counter = base_slug, 1
        while QRCode.objects.filter(restaurant=restaurant, slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        qr = QRCode.objects.create(restaurant=restaurant, label=label, slug=slug)
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
            {"key": "dark",  "name": "Dark Elegant",
             "desc": "Gold & black luxury design — perfect for fine dining",
             "preview_bg": "#0A0A0A", "preview_accent": "#C9A84C"},
            {"key": "white", "name": "Fresh White",
             "desc": "Red & white bold design — great for cafes & casual dining",
             "preview_bg": "#E63946", "preview_accent": "#FFFFFF"},
            {"key": "bold",  "name": "Bold Street",
             "desc": "Yellow & black high-contrast — ideal for fast food & modern restaurants",
             "preview_bg": "#1A1A1A", "preview_accent": "#FFB703"},
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

    scan_url     = request.build_absolute_uri(qr.get_scan_url())
    qr_img       = _make_qr(scan_url, size=400)
    tpl_name, fn = TEMPLATES[template_key]
    canvas       = fn(qr_img, restaurant.name, qr.label)

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

write('apps/qrcodes/views.py', qr_views)

# ══════════════════════════════════════════════════════════════
# 2.  QR Template Picker — redesigned
# ══════════════════════════════════════════════════════════════

picker_html = """{% extends "base.html" %}
{% block title %}Download QR — {{ qr.label }}{% endblock %}
{% block content %}
<div class="page">

  <div class="breadcrumb">
    <a href="{% url 'dashboard' %}">Dashboard</a>
    <span class="breadcrumb__sep">›</span>
    <a href="{% url 'qr_list' %}">QR Codes</a>
    <span class="breadcrumb__sep">›</span>
    <span class="breadcrumb__current">Download — {{ qr.label }}</span>
  </div>

  <div class="page-header">
    <div>
      <h1 class="page-header__title">Choose a Print Template</h1>
      <p class="page-header__sub">
        QR code for <strong>{{ qr.label }}</strong> ·
        Scanned <strong>{{ qr.scan_count }}</strong> time{{ qr.scan_count|pluralize }}
      </p>
    </div>
    <a href="{% url 'qr_list' %}" class="btn btn--ghost btn--sm">← Back</a>
  </div>

  <div class="alert alert--info mb-3">
    ℹ Each template has your restaurant name and table label already embedded.
    Download the PNG and print at <strong>A5 size</strong> for best results.
    Laminate for spill protection.
  </div>

  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.5rem;">

    {% for tpl in templates %}
    <div class="card" style="overflow:hidden;border:2px solid var(--border);
                              transition:all 0.25s;"
         onmouseover="this.style.transform='translateY(-4px)';this.style.borderColor='var(--brand)';this.style.boxShadow='0 12px 40px rgba(0,0,0,0.12)'"
         onmouseout="this.style.transform='';this.style.borderColor='var(--border)';this.style.boxShadow=''">

      <!-- Template visual preview -->
      <div style="background:{{ tpl.preview_bg }};min-height:200px;
                  display:flex;flex-direction:column;align-items:center;
                  justify-content:center;gap:0.75rem;padding:2rem;
                  position:relative;overflow:hidden;">

        <!-- Decorative bg -->
        <div style="position:absolute;top:-20px;right:-20px;width:100px;height:100px;
                    border-radius:50%;border:2px solid {{ tpl.preview_accent }};opacity:0.2;"></div>
        <div style="position:absolute;bottom:-30px;left:-30px;width:120px;height:120px;
                    border-radius:50%;border:2px solid {{ tpl.preview_accent }};opacity:0.15;"></div>

        <!-- Restaurant name mockup -->
        <div style="font-family:Georgia,serif;font-weight:700;
                    color:{{ tpl.preview_accent }};font-size:1.1rem;
                    text-align:center;letter-spacing:0.05em;position:relative;">
          {{ qr.restaurant.name|upper|truncatechars:20 }}
        </div>

        <!-- QR placeholder -->
        <div style="width:80px;height:80px;background:white;border-radius:8px;
                    display:flex;align-items:center;justify-content:center;
                    border:3px solid {{ tpl.preview_accent }};position:relative;">
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2px;padding:6px;">
            {% for i in "123456789" %}
              <div style="width:10px;height:10px;background:#333;border-radius:1px;
                          opacity:{% cycle '1' '0.3' '1' '0.3' '1' '0.3' '1' '0.3' '1' %};"></div>
            {% endfor %}
          </div>
        </div>

        <!-- Table label -->
        <div style="background:{{ tpl.preview_accent }};color:{{ tpl.preview_bg }};
                    padding:0.25rem 0.85rem;border-radius:100px;
                    font-size:0.75rem;font-weight:700;position:relative;">
          {{ qr.label }}
        </div>

      </div>

      <!-- Card info -->
      <div class="card__body">
        <div style="font-weight:700;font-size:1rem;margin-bottom:0.3rem;">
          {{ tpl.name }}
        </div>
        <div style="font-size:0.825rem;color:var(--muted);margin-bottom:1.25rem;
                    line-height:1.5;">
          {{ tpl.desc }}
        </div>
        <a href="{% url 'qr_download_template' qr.pk tpl.key %}"
           class="btn btn--primary btn--full">
          ⬇ Download {{ tpl.name }}
        </a>
      </div>
    </div>
    {% endfor %}

  </div>

  <!-- Print tips -->
  <div class="card mt-3" style="background:#FFFBEA;border-color:#FCD34D;">
    <div class="card__body">
      <div style="font-weight:700;font-size:0.9rem;color:#92400E;margin-bottom:0.5rem;">
        💡 Printing Tips
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0.75rem;">
        <div style="font-size:0.825rem;color:#92400E;">
          📐 <strong>Print size:</strong> A5 or A6 for table cards. A4 for wall posters.
        </div>
        <div style="font-size:0.825rem;color:#92400E;">
          🛡 <strong>Laminate it:</strong> Makes it waterproof and spill-proof.
        </div>
        <div style="font-size:0.825rem;color:#92400E;">
          📱 <strong>Test first:</strong> Scan the downloaded PNG with your phone before printing.
        </div>
        <div style="font-size:0.825rem;color:#92400E;">
          🖨 <strong>Best quality:</strong> Print at 300 DPI for sharp QR codes.
        </div>
      </div>
    </div>
  </div>

</div>
{% endblock %}"""

write('templates/qrcodes/qr_template_picker.html', picker_html)

# ══════════════════════════════════════════════════════════════
# 3.  Redesigned public customer menu
# ══════════════════════════════════════════════════════════════

public_menu_html = """{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ restaurant.name }} — Menu</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --brand:     {{ restaurant.theme_color }};
      --brand-rgb: 230, 57, 70;
      --font-d: 'Playfair Display', Georgia, serif;
      --font-b: 'DM Sans', sans-serif;
    }
    * { box-sizing:border-box; margin:0; padding:0; }
    html { scroll-behavior:smooth; }
    body { font-family:var(--font-b); background:#F8F7F4;
           color:#1A1A1A; padding-bottom:2rem; }

    /* ── HERO HEADER ─────────────────────────── */
    .menu-hero {
      background: linear-gradient(160deg, var(--brand) 0%, color-mix(in srgb, var(--brand) 70%, #000) 100%);
      padding: 2.5rem 1.25rem 3.5rem;
      text-align: center;
      position: relative;
      overflow: hidden;
    }
    .menu-hero::before {
      content:'';
      position:absolute; inset:0;
      background: radial-gradient(ellipse 80% 60% at 50% 0%,
                  rgba(255,255,255,0.12) 0%, transparent 70%);
    }
    .menu-hero::after {
      content:'';
      position:absolute; bottom:-2px; left:0; right:0; height:32px;
      background:#F8F7F4;
      clip-path: ellipse(55% 100% at 50% 100%);
    }
    .hero-logo {
      width: 80px; height: 80px;
      border-radius: 50%; object-fit: cover;
      border: 3px solid rgba(255,255,255,0.4);
      box-shadow: 0 4px 20px rgba(0,0,0,0.2);
      margin: 0 auto 0.85rem;
      display: block; position: relative;
    }
    .hero-logo-placeholder {
      width: 72px; height: 72px; border-radius: 50%;
      background: rgba(255,255,255,0.15);
      display: flex; align-items: center; justify-content: center;
      font-size: 2rem; margin: 0 auto 0.85rem; position: relative;
    }
    .hero-name {
      font-family: var(--font-d);
      font-size: 2rem; font-weight: 700;
      color: #fff; position: relative;
      text-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .hero-desc {
      font-size: 0.875rem; color: rgba(255,255,255,0.75);
      margin-top: 0.4rem; position: relative;
    }
    .hero-info {
      display: flex; gap: 1.25rem; justify-content: center;
      margin-top: 0.85rem; position: relative;
    }
    .hero-info span {
      font-size: 0.78rem; color: rgba(255,255,255,0.65);
      display: flex; align-items: center; gap: 0.3rem;
    }

    /* ── CATEGORY TABS ───────────────────────── */
    .cat-tabs {
      position: sticky; top: 0; z-index: 50;
      background: #fff;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      overflow-x: auto; -webkit-overflow-scrolling: touch;
    }
    .cat-tabs::-webkit-scrollbar { display: none; }
    .cat-tabs-inner {
      display: flex; gap: 0; padding: 0 0.5rem;
      white-space: nowrap; min-width: max-content;
    }
    .cat-tab {
      padding: 0.85rem 1.1rem;
      font-size: 0.85rem; font-weight: 500;
      color: #888; border-bottom: 3px solid transparent;
      cursor: pointer; text-decoration: none;
      transition: all 0.2s; display: inline-block;
      white-space: nowrap;
    }
    .cat-tab:hover { color: var(--brand); }
    .cat-tab.active {
      color: var(--brand);
      border-bottom-color: var(--brand);
      font-weight: 600;
    }

    /* ── MENU SECTIONS ───────────────────────── */
    .menu-body { padding: 0 0.75rem; }

    .menu-section { padding: 1.5rem 0 0.5rem; }
    .section-header {
      display: flex; align-items: center; gap: 0.75rem;
      margin-bottom: 1rem;
    }
    .section-title {
      font-family: var(--font-d);
      font-size: 1.3rem; font-weight: 700;
      color: #1A1A1A;
    }
    .section-line {
      flex: 1; height: 1px;
      background: linear-gradient(90deg, var(--brand), transparent);
      opacity: 0.3;
    }
    .section-count {
      font-size: 0.75rem; color: #aaa;
      background: #f0f0f0; padding: 0.15rem 0.5rem;
      border-radius: 100px;
    }

    /* ── ITEM CARDS ──────────────────────────── */
    .item-card {
      background: #fff;
      border-radius: 16px;
      margin-bottom: 0.75rem;
      display: flex;
      overflow: hidden;
      box-shadow: 0 1px 6px rgba(0,0,0,0.06);
      border: 1px solid #F0EDE8;
      transition: all 0.2s;
      position: relative;
    }
    .item-card:hover {
      box-shadow: 0 6px 20px rgba(0,0,0,0.1);
      transform: translateY(-1px);
    }
    .item-img {
      width: 100px; flex-shrink: 0;
      object-fit: cover; display: block;
    }
    .item-img-placeholder {
      width: 100px; flex-shrink: 0;
      background: linear-gradient(135deg, #F8F7F4, #EDE9E3);
      display: flex; align-items: center;
      justify-content: center; font-size: 1.75rem;
    }
    .item-body { padding: 0.9rem 1rem; flex: 1; display: flex;
                 flex-direction: column; justify-content: space-between; }
    .item-top  { display: flex; justify-content: space-between;
                 align-items: flex-start; gap: 0.5rem; }
    .item-name {
      font-weight: 600; font-size: 0.95rem;
      color: #1A1A1A; line-height: 1.3;
    }
    .item-badges { display: flex; gap: 0.3rem; flex-wrap: wrap; margin-top: 0.3rem; }
    .badge {
      font-size: 0.68rem; font-weight: 700;
      padding: 0.15rem 0.45rem; border-radius: 4px;
      display: inline-flex; align-items: center; gap: 0.2rem;
    }
    .badge-popular { background: #FEF9C3; color: #854D0E; }
    .badge-new     { background: #DCFCE7; color: #166534; }
    .item-desc {
      font-size: 0.8rem; color: #999;
      margin-top: 0.4rem; line-height: 1.5;
      display: -webkit-box; -webkit-line-clamp: 2;
      -webkit-box-orient: vertical; overflow: hidden;
    }
    .item-footer {
      display: flex; align-items: center;
      justify-content: space-between; margin-top: 0.6rem;
    }
    .item-price {
      font-family: var(--font-d);
      font-size: 1.1rem; font-weight: 700;
      color: var(--brand);
    }
    .item-price-label {
      font-size: 0.7rem; color: #bbb;
      font-family: var(--font-b); font-weight: 400;
    }

    /* ── EMPTY STATE ─────────────────────────── */
    .empty-menu {
      text-align: center; padding: 4rem 1.5rem;
    }
    .empty-menu .icon { font-size: 3rem; opacity: 0.3; margin-bottom: 1rem; }
    .empty-menu p { color: #aaa; font-size: 0.9rem; }

    /* ── FOOTER ──────────────────────────────── */
    .menu-footer {
      text-align: center; padding: 2rem 1rem 1rem;
      color: #ccc; font-size: 0.75rem;
    }
  </style>
</head>
<body>

<!-- Hero Header -->
<div class="menu-hero">
  {% if restaurant.logo %}
    <img src="{{ restaurant.logo.url }}" alt="{{ restaurant.name }}" class="hero-logo">
  {% else %}
    <div class="hero-logo-placeholder">🍽</div>
  {% endif %}
  <h1 class="hero-name">{{ restaurant.name }}</h1>
  {% if restaurant.description %}
    <p class="hero-desc">{{ restaurant.description }}</p>
  {% endif %}
  <div class="hero-info">
    {% if restaurant.phone %}
      <span>📞 {{ restaurant.phone }}</span>
    {% endif %}
    {% if restaurant.address %}
      <span>📍 {{ restaurant.address|truncatechars:30 }}</span>
    {% endif %}
  </div>
</div>

<!-- Category Tabs -->
{% if categories %}
<div class="cat-tabs">
  <div class="cat-tabs-inner">
    {% for cat in categories %}
      <a href="#sec-{{ cat.pk }}"
         class="cat-tab"
         data-cat="{{ cat.pk }}">
        {{ cat.name }}
      </a>
    {% endfor %}
  </div>
</div>
{% endif %}

<!-- Menu Body -->
<div class="menu-body">
  {% for cat in categories %}
    {% with items=cat.items.all %}
    <div class="menu-section" id="sec-{{ cat.pk }}">
      <div class="section-header">
        <h2 class="section-title">{{ cat.name }}</h2>
        <div class="section-line"></div>
        <span class="section-count">{{ items|length }}</span>
      </div>

      {% for item in items %}
        {% if item.is_available %}
        <div class="item-card">

          {% if item.image %}
            <img src="{{ item.image.url }}" alt="{{ item.name }}" class="item-img">
          {% else %}
            <div class="item-img-placeholder">🍴</div>
          {% endif %}

          <div class="item-body">
            <div>
              <div class="item-top">
                <span class="item-name">{{ item.name }}</span>
              </div>
              <div class="item-badges">
                {% if item.is_popular %}
                  <span class="badge badge-popular">⭐ Popular</span>
                {% endif %}
              </div>
              {% if item.description %}
                <p class="item-desc">{{ item.description }}</p>
              {% endif %}
            </div>
            <div class="item-footer">
              <div>
                <div class="item-price-label">Price</div>
                <div class="item-price">₹{{ item.price }}</div>
              </div>
            </div>
          </div>

        </div>
        {% endif %}
      {% empty %}
        <p style="color:#bbb;font-size:0.85rem;padding:0.5rem 0;">
          No items in this category yet.
        </p>
      {% endfor %}
    </div>
    {% endwith %}
  {% empty %}
    <div class="empty-menu">
      <div class="icon">🍽</div>
      <p>Menu coming soon!</p>
    </div>
  {% endfor %}
</div>

<!-- Footer -->
<div class="menu-footer">
  <p>{{ restaurant.name }} · Digital Menu</p>
  <p style="margin-top:0.25rem;">Powered by QR Menu</p>
</div>

<script>
  // Highlight tab on scroll
  const sections = document.querySelectorAll('.menu-section[id]');
  const tabs     = document.querySelectorAll('.cat-tab');

  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const id = e.target.id.replace('sec-','');
        tabs.forEach(t => t.classList.toggle('active', t.dataset.cat === id));
      }
    });
  }, { rootMargin: '-25% 0px -65% 0px' });

  sections.forEach(s => obs.observe(s));

  tabs.forEach(tab => {
    tab.addEventListener('click', e => {
      e.preventDefault();
      const target = document.querySelector(tab.getAttribute('href'));
      if (target) {
        const offset = 60;
        const top    = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });
</script>
</body>
</html>"""

write('templates/menus/public_menu.html', public_menu_html)

print("\n" + "=" * 60)
print("ALL DONE!")
print("=" * 60)
print("""
Changes made:
  ✓ 3 completely redesigned QR templates:
      - Dark Elegant  (gold & black luxury, fine dining)
      - Fresh White   (red & white bold, cafes)
      - Bold Street   (yellow & black, modern/fast food)
  ✓ Restaurant name + table label clearly visible on all templates
  ✓ Beautiful new template picker UI with live color previews
  ✓ Redesigned customer menu with:
      - Large hero header with restaurant branding
      - Sticky scrollable category tabs
      - Beautiful item cards with images
      - Section dividers with item counts
      - Smooth scroll tab highlighting

Restart server:
  python manage.py runserver

Then test:
  QR download:   http://127.0.0.1:8000/qr/
  Public menu:   http://127.0.0.1:8000/m/cafe-delight/

Deploy:
  git add .
  git commit -m "Redesign QR templates and public menu"
  git push origin main
""")

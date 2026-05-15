"""
Run from project root:  python apply_final_templates.py
Applies the exact 3 QR templates provided by the user.
"""
import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
print("=" * 60)
print("QR Menu — Applying Final QR Templates")
print("=" * 60)

def write(rel, content):
    path = os.path.join(BASE, rel.replace('/', os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✓ {rel}")

# ══════════════════════════════════════════════════════════════
# apps/qrcodes/views.py — exact templates from user
# ══════════════════════════════════════════════════════════════

views = r'''import io
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


def _make_qr(url, size=500):
    """Generate QR code — HIGH error correction so center badge doesn't break scan."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)
    return img


def _embed_name_in_qr(qr_img, text, bg="#E63946", fg="#FFFFFF"):
    """
    Embed restaurant name as a pill badge in the center of the QR.
    ERROR_CORRECT_H allows up to 30% of QR to be obscured — badge is ~20%.
    """
    W, H   = qr_img.size
    cx, cy = W // 2, H // 2

    badge_w = int(W * 0.44)
    badge_h = int(H * 0.13)
    bx      = cx - badge_w // 2
    by      = cy - badge_h // 2

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d       = ImageDraw.Draw(overlay)

    # White halo behind badge for contrast
    d.rounded_rectangle(
        [bx - 5, by - 5, bx + badge_w + 5, by + badge_h + 5],
        radius=(badge_h + 10) // 2,
        fill="#FFFFFF"
    )
    # Coloured badge
    d.rounded_rectangle(
        [bx, by, bx + badge_w, by + badge_h],
        radius=badge_h // 2,
        fill=bg
    )

    # Text — truncate to fit
    short = text[:15]
    font_size = badge_h - 14
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                font_size
            )
        except:
            font = ImageFont.load_default()

    bbox = d.textbbox((0, 0), short, font=font)
    tw   = bbox[2] - bbox[0]
    th   = bbox[3] - bbox[1]
    tx   = cx - tw // 2
    ty   = by + (badge_h - th) // 2 - bbox[1]
    d.text((tx, ty), short, fill=fg, font=font)

    result = Image.alpha_composite(qr_img.convert("RGBA"), overlay)
    return result.convert("RGBA")


# ══════════════════════════════════════════════════════════════
# TEMPLATE 1 : FRESH WHITE
# ══════════════════════════════════════════════════════════════
def _tpl_fresh_white(qr_img, restaurant_name, table_label):
    W, H = 700, 1050
    img  = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    try:
        font_scan   = ImageFont.truetype("arialbd.ttf",  52)
        font_name   = ImageFont.truetype("arialbd.ttf",  70)
        font_for    = ImageFont.truetype("arialbd.ttf",  46)
        font_menu   = ImageFont.truetype("arialbd.ttf",  90)
        font_table  = ImageFont.truetype("arialbd.ttf",  28)
        font_footer = ImageFont.truetype("arial.ttf",    22)
        font_power  = ImageFont.truetype("arialbd.ttf",  22)
    except:
        font_scan = font_name = font_for = font_menu = \
        font_table = font_footer = font_power = ImageFont.load_default()

    # Top banner
    draw.rectangle([0, 0, W, 240], fill="#E63946")

    # Decorative circles
    draw.ellipse([-60, -60, 120, 120], outline="#FF8A95", width=4)
    draw.ellipse([-30, -30,  90,  90], outline="#FF8A95", width=3)
    draw.ellipse([W-120, -60, W+60, 120], outline="#FF8A95", width=4)

    draw.text((W//2,  70), "SCAN HERE",              fill="#FFFFFF", font=font_scan,  anchor="mm")
    draw.text((W//2, 155), restaurant_name.upper(),  fill="#FFFFFF", font=font_name,  anchor="mm")

    # Dark stripe
    draw.rectangle([0, 240, W, 252], fill="#C1121F")

    draw.text((W//2, 330), "FOR OUR", fill="#666666", font=font_for,  anchor="mm")
    draw.text((W//2, 445), "MENU",    fill="#E63946", font=font_menu, anchor="mm")

    # Dotted line
    for x in range(60, W - 60, 18):
        draw.rectangle([x, 520, x + 10, 524], fill="#E63946")

    # QR — embed name badge in center (red badge, white text)
    qr_with_name = _embed_name_in_qr(qr_img.copy(), restaurant_name,
                                      bg="#E63946", fg="#FFFFFF")
    qr_size = 300
    qr_x    = (W - qr_size) // 2
    qr_y    = 540

    # Shadow
    draw.rounded_rectangle(
        [qr_x + 10, qr_y + 10, qr_x + qr_size + 10, qr_y + qr_size + 10],
        radius=12, fill="#E0E0E0"
    )
    # White card
    draw.rounded_rectangle(
        [qr_x - 20, qr_y - 20, qr_x + qr_size + 20, qr_y + qr_size + 20],
        radius=16, fill="#FFFFFF", outline="#DDDDDD", width=2
    )

    qr_resized = qr_with_name.resize((qr_size, qr_size), Image.LANCZOS)
    if qr_resized.mode == "RGBA":
        img.paste(qr_resized, (qr_x, qr_y), qr_resized)
    else:
        img.paste(qr_resized, (qr_x, qr_y))

    # Table badge
    badge_y = qr_y + qr_size + 45
    badge_w = 260
    badge_x = (W - badge_w) // 2
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w, badge_y + 52],
        radius=26, fill="#E63946"
    )
    draw.text((W//2, badge_y + 26), table_label, fill="#FFFFFF",
              font=font_table, anchor="mm")

    draw.text((W//2, badge_y + 95),  "Open your camera & point at the QR code",
              fill="#777777", font=font_footer, anchor="mm")
    draw.text((W//2, badge_y + 135), "No app download required",
              fill="#AAAAAA", font=font_footer, anchor="mm")

    draw.rectangle([0, H - 60, W, H], fill="#E63946")
    draw.text((W//2, H - 30), "Powered by QR Menu",
              fill="#FFFFFF", font=font_power, anchor="mm")

    return img


# ══════════════════════════════════════════════════════════════
# TEMPLATE 2 : LUXURY BLACK & GOLD
# ══════════════════════════════════════════════════════════════
def _tpl_luxury_black(qr_img, restaurant_name, table_label):
    W, H = 700, 1050
    img  = Image.new("RGB", (W, H), "#000000")
    draw = ImageDraw.Draw(img)
    gold = "#D4AF37"

    try:
        font_top    = ImageFont.truetype("arial.ttf",   28)
        font_name   = ImageFont.truetype("arialbd.ttf", 64)
        font_scan   = ImageFont.truetype("arialbd.ttf", 34)
        font_table  = ImageFont.truetype("arialbd.ttf", 32)
        font_footer = ImageFont.truetype("arial.ttf",   24)
    except:
        font_top = font_name = font_scan = \
        font_table = font_footer = ImageFont.load_default()

    # Gold outer border
    draw.rectangle([8, 8, W - 8, H - 8], outline=gold, width=6)

    # Corner decorations
    for (x1, y1, x2, y2) in [
        (20, 20, 120, 20), (20, 20, 20, 120),
        (W-120, 20, W-20, 20), (W-20, 20, W-20, 120),
        (20, H-20, 120, H-20), (20, H-120, 20, H-20),
        (W-120, H-20, W-20, H-20), (W-20, H-120, W-20, H-20),
    ]:
        draw.line([(x1, y1), (x2, y2)], fill=gold, width=3)

    draw.text((W//2, 120), "WELCOME TO",            fill=gold,     font=font_top,  anchor="mm")
    draw.text((W//2, 190), restaurant_name.upper(), fill="#FFFFFF", font=font_name, anchor="mm")

    # Gold divider + diamond
    draw.line([80, 290, W - 80, 290], fill=gold, width=2)
    cx = W // 2
    draw.polygon([(cx, 278), (cx+12, 290), (cx, 302), (cx-12, 290)], fill=gold)

    draw.text((W//2, 350), "SCAN FOR OUR MENU", fill="#BBBBBB", font=font_scan, anchor="mm")

    # QR — embed name with gold badge
    qr_with_name = _embed_name_in_qr(qr_img.copy(), restaurant_name,
                                      bg="#D4AF37", fg="#000000")
    qr_size = 360
    qr_x    = (W - qr_size) // 2
    qr_y    = 400

    draw.rounded_rectangle(
        [qr_x - 18, qr_y - 18, qr_x + qr_size + 18, qr_y + qr_size + 18],
        radius=12, outline=gold, width=5
    )
    # White bg for QR
    draw.rectangle([qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], fill="#FFFFFF")

    qr_resized = qr_with_name.resize((qr_size, qr_size), Image.LANCZOS)
    if qr_resized.mode == "RGBA":
        img.paste(qr_resized, (qr_x, qr_y), qr_resized)
    else:
        img.paste(qr_resized, (qr_x, qr_y))

    draw.line([80, 820, W - 80, 820], fill="#333333", width=2)

    # Table badge (outlined gold, no fill)
    badge_w, badge_h = 320, 60
    badge_x = (W - badge_w) // 2
    badge_y = 848
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
        radius=30, outline=gold, width=3
    )
    draw.text((W//2, badge_y + badge_h // 2), table_label.upper(),
              fill=gold, font=font_table, anchor="mm")

    draw.text((W//2, 960), "NO APP NEEDED • JUST SCAN",
              fill="#666666", font=font_footer, anchor="mm")

    return img


# ══════════════════════════════════════════════════════════════
# TEMPLATE 3 : MODERN YELLOW & BLACK
# ══════════════════════════════════════════════════════════════
def _tpl_modern_yellow(qr_img, restaurant_name, table_label):
    W, H   = 700, 1050
    img    = Image.new("RGB", (W, H), "#111111")
    draw   = ImageDraw.Draw(img)
    yellow = "#FFB800"

    # Diagonal yellow top polygon
    draw.polygon([(0, 0), (W, 0), (W, 320), (0, 200)], fill=yellow)
    # Yellow bottom strip
    draw.rectangle([0, H - 45, W, H], fill=yellow)

    try:
        font_small  = ImageFont.truetype("arial.ttf",   28)
        font_big    = ImageFont.truetype("arialbd.ttf", 76)
        font_name   = ImageFont.truetype("arialbd.ttf", 42)
        font_scan   = ImageFont.truetype("arialbd.ttf", 36)
        font_table  = ImageFont.truetype("arialbd.ttf", 30)
        font_footer = ImageFont.truetype("arial.ttf",   24)
    except:
        font_small = font_big = font_name = font_scan = \
        font_table = font_footer = ImageFont.load_default()

    draw.text((W//2, 100), "VIEW OUR",              fill="#000000", font=font_small, anchor="mm")
    draw.text((W//2, 180), "MENU",                  fill="#000000", font=font_big,   anchor="mm")
    draw.line([310, 250, 390, 250], fill="#000000", width=5)
    draw.text((W//2, 310), restaurant_name.upper(), fill="#000000", font=font_name,  anchor="mm")
    draw.text((W//2, 420), "SCAN HERE",             fill="#FFFFFF", font=font_scan,  anchor="mm")
    draw.text((180,  420), "✦",                     fill=yellow,    font=font_scan,  anchor="mm")
    draw.text((520,  420), "✦",                     fill=yellow,    font=font_scan,  anchor="mm")

    # QR — embed name with yellow badge
    qr_with_name = _embed_name_in_qr(qr_img.copy(), restaurant_name,
                                      bg="#FFB800", fg="#000000")
    qr_size = 340
    qr_x    = (W - qr_size) // 2
    qr_y    = 480

    draw.rounded_rectangle(
        [qr_x - 16, qr_y - 16, qr_x + qr_size + 16, qr_y + qr_size + 16],
        radius=14, fill=yellow
    )
    draw.rounded_rectangle(
        [qr_x - 2, qr_y - 2, qr_x + qr_size + 2, qr_y + qr_size + 2],
        radius=10, fill="#FFFFFF"
    )

    qr_resized = qr_with_name.resize((qr_size, qr_size), Image.LANCZOS)
    if qr_resized.mode == "RGBA":
        img.paste(qr_resized, (qr_x, qr_y), qr_resized)
    else:
        img.paste(qr_resized, (qr_x, qr_y))

    # Table badge
    badge_w, badge_h = 360, 70
    badge_x = (W - badge_w) // 2
    badge_y = qr_y + qr_size + 40
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
        radius=35, fill=yellow
    )
    draw.text((W//2, badge_y + badge_h // 2), table_label.upper(),
              fill="#000000", font=font_table, anchor="mm")

    draw.text((W//2, badge_y + badge_h + 40), restaurant_name.upper(),
              fill="#000000", font=font_footer, anchor="mm")

    return img


# ══════════════════════════════════════════════════════════════
# TEMPLATE REGISTRY
# ══════════════════════════════════════════════════════════════
TEMPLATES = {
    "white":  ("Fresh White",       _tpl_fresh_white),
    "black":  ("Luxury Black Gold", _tpl_luxury_black),
    "yellow": ("Modern Yellow",     _tpl_modern_yellow),
}


# ══════════════════════════════════════════════════════════════
# VIEWS
# ══════════════════════════════════════════════════════════════

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
            messages.error(request, "Please enter a label.")
            return render(request, "qrcodes/qr_form.html", {"label_value": ""})

        base_slug = slugify(label) or \
                    f"qr-{QRCode.objects.filter(restaurant=restaurant).count() + 1}"
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
            {
                "key":   "white",
                "name":  "Fresh White",
                "desc":  "Bold red & white — great for cafes and casual dining",
                "top":   "#E63946",
                "body":  "#FFFFFF",
                "accent":"#E63946",
                "text":  "#FFFFFF",
            },
            {
                "key":   "black",
                "name":  "Luxury Black & Gold",
                "desc":  "Elegant gold on black — perfect for fine dining",
                "top":   "#000000",
                "body":  "#000000",
                "accent":"#D4AF37",
                "text":  "#D4AF37",
            },
            {
                "key":   "yellow",
                "name":  "Modern Yellow & Black",
                "desc":  "High-contrast yellow — ideal for modern restaurants",
                "top":   "#FFB800",
                "body":  "#111111",
                "accent":"#FFB800",
                "text":  "#000000",
            },
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
    qr_img        = _make_qr(scan_url, size=500)
    tpl_name, fn  = TEMPLATES[template_key]
    canvas        = fn(qr_img, restaurant.name, qr.label)

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

write('apps/qrcodes/views.py', views)

# ══════════════════════════════════════════════════════════════
# Template picker — shows all 3 accurate previews
# ══════════════════════════════════════════════════════════════

write('templates/qrcodes/qr_template_picker.html', """{% extends "base.html" %}
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
      <h1 class="page-header__title">Choose Print Template</h1>
      <p class="page-header__sub">
        Restaurant name is printed on the card and inside the QR code
      </p>
    </div>
    <a href="{% url 'qr_list' %}" class="btn btn--ghost btn--sm">← Back</a>
  </div>

  <div class="alert alert--info mb-3">
    ℹ All templates include your <strong>restaurant name</strong> and
    <strong>{{ qr.label }}</strong>. Print at <strong>A5</strong> size and laminate.
  </div>

  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1.5rem;">
  {% for tpl in templates %}

    <div style="border-radius:16px;overflow:hidden;
                box-shadow:0 4px 20px rgba(0,0,0,0.12);
                transition:all 0.25s;cursor:pointer;"
         onmouseover="this.style.transform='translateY(-5px)';this.style.boxShadow='0 16px 48px rgba(0,0,0,0.2)'"
         onmouseout="this.style.transform='';this.style.boxShadow='0 4px 20px rgba(0,0,0,0.12)'">

      <!-- Top banner preview -->
      <div style="background:{{ tpl.top }};padding:1.25rem 1rem;
                  text-align:center;position:relative;overflow:hidden;">
        <!-- Deco circles (Fresh White only) -->
        {% if tpl.key == 'white' %}
          <div style="position:absolute;top:-30px;left:-30px;width:80px;height:80px;
                      border-radius:50%;border:3px solid #FF8A95;opacity:0.5;"></div>
          <div style="position:absolute;top:-30px;right:-30px;width:80px;height:80px;
                      border-radius:50%;border:3px solid #FF8A95;opacity:0.5;"></div>
        {% endif %}

        <div style="font-size:0.78rem;font-weight:700;
                    color:{{ tpl.text }};letter-spacing:0.12em;
                    margin-bottom:0.3rem;position:relative;">
          SCAN HERE
        </div>
        <div style="font-size:1rem;font-weight:800;
                    color:{{ tpl.text }};letter-spacing:0.05em;
                    position:relative;">
          {{ qr.restaurant.name|upper|truncatechars:20 }}
        </div>
      </div>

      <!-- Accent stripe -->
      <div style="height:6px;background:{% if tpl.key == 'white' %}#C1121F
                  {% elif tpl.key == 'black' %}#D4AF37
                  {% else %}#FFB800{% endif %};"></div>

      <!-- Body preview -->
      <div style="background:{{ tpl.body }};padding:1rem;text-align:center;">

        {% if tpl.key != 'yellow' %}
          <div style="font-size:0.72rem;letter-spacing:0.08em;
                      color:{% if tpl.key == 'white' %}#666{% else %}#BBB{% endif %};
                      margin-bottom:0.2rem;">FOR OUR</div>
          <div style="font-size:1.5rem;font-weight:900;
                      color:{{ tpl.accent }};margin-bottom:0.6rem;">MENU</div>
        {% else %}
          <div style="font-size:0.72rem;color:#888;margin-bottom:0.2rem;">VIEW OUR</div>
          <div style="font-size:1.5rem;font-weight:900;
                      color:{{ tpl.accent }};margin-bottom:0.6rem;">MENU</div>
        {% endif %}

        <!-- QR placeholder with name badge -->
        <div style="width:100px;height:100px;background:#fff;
                    border-radius:10px;margin:0 auto;position:relative;
                    display:flex;align-items:center;justify-content:center;
                    {% if tpl.key == 'black' %}
                      border:3px solid #D4AF37;
                    {% elif tpl.key == 'yellow' %}
                      outline:4px solid #FFB800;
                    {% else %}
                      box-shadow:0 4px 12px rgba(0,0,0,0.15);
                    {% endif %}">
          <!-- Fake QR dots -->
          <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:2px;padding:6px;width:100%;height:100%;">
            {% for i in "123456789012345678901234567890123456" %}
              <div style="border-radius:1px;background:{% cycle '#000' '#fff' '#000' '#000' '#fff' '#000' '#fff' '#000' '#000' '#fff' '#000' '#fff' %};"></div>
            {% endfor %}
          </div>
          <!-- Name badge in center -->
          <div style="position:absolute;background:{{ tpl.accent }};
                      color:{{ tpl.text }};padding:0.1rem 0.4rem;
                      border-radius:100px;font-size:0.5rem;font-weight:700;
                      white-space:nowrap;max-width:80px;overflow:hidden;
                      text-overflow:ellipsis;">
            {{ qr.restaurant.name|truncatechars:10 }}
          </div>
        </div>

        <!-- Table badge -->
        <div style="display:inline-block;margin-top:0.75rem;
                    background:{{ tpl.accent }};color:{{ tpl.text }};
                    padding:0.3rem 1rem;border-radius:100px;
                    font-size:0.75rem;font-weight:700;
                    {% if tpl.key == 'black' %}
                      background:transparent;border:2px solid #D4AF37;color:#D4AF37;
                    {% endif %}">
          {{ qr.label }}
        </div>

      </div>

      <!-- Download button -->
      <a href="{% url 'qr_download_template' qr.pk tpl.key %}"
         style="display:block;background:{{ tpl.accent }};color:{{ tpl.text }};
                padding:0.85rem;text-align:center;font-weight:700;
                font-size:0.9rem;text-decoration:none;
                border-top:1px solid rgba(0,0,0,0.08);">
        ⬇ Download {{ tpl.name }}
      </a>

    </div>
  {% endfor %}
  </div>

  <!-- Tips -->
  <div style="background:#FFFBEA;border:1px solid #FCD34D;border-radius:12px;
              padding:1rem 1.25rem;margin-top:1.5rem;">
    <div style="font-weight:700;color:#92400E;margin-bottom:0.5rem;">💡 Printing Tips</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:0.5rem;">
      <div style="font-size:0.82rem;color:#92400E;">📐 Print at <strong>A5</strong> for table cards</div>
      <div style="font-size:0.82rem;color:#92400E;">🛡 <strong>Laminate</strong> for spill protection</div>
      <div style="font-size:0.82rem;color:#92400E;">📱 <strong>Test scan</strong> before bulk printing</div>
      <div style="font-size:0.82rem;color:#92400E;">🖨 Use <strong>300 DPI</strong> for sharp QR code</div>
    </div>
  </div>

</div>
{% endblock %}""")

# ── Also update urls.py with new keys ────────────────────────
write('apps/qrcodes/urls.py', """from django.urls import path
from . import views

urlpatterns = [
    path('',                                      views.qr_list,              name='qr_list'),
    path('new/',                                  views.qr_create,            name='qr_create'),
    path('<int:pk>/download/',                    views.qr_download,          name='qr_download'),
    path('<int:pk>/download/<str:template_key>/', views.qr_download_template, name='qr_download_template'),
    path('<int:pk>/delete/',                      views.qr_delete,            name='qr_delete'),
]
""")

print("\n" + "=" * 60)
print("DONE! Restart server:")
print("  python manage.py runserver")
print()
print("Test QR download at: http://127.0.0.1:8000/qr/")
print()
print("Deploy:")
print("  git add .")
print('  git commit -m "Apply final QR templates"')
print("  git push origin main")
print("=" * 60)

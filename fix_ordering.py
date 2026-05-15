"""
Run from project root:  python fix_ordering.py
Fixes QR scan → ordering page with Add to Cart buttons.
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
print("=" * 60)
print("QR Menu — Fixing Order Flow + Add to Cart Buttons")
print("=" * 60)

def write(rel, content):
    path = os.path.join(BASE, rel.replace('/', os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✓ {rel}")

# ══════════════════════════════════════════════════════════════
# 1. Fix public_views.py — QR scan redirects to ordering page
# ══════════════════════════════════════════════════════════════

write('apps/menus/public_views.py', '''import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils import timezone
from apps.restaurants.models import Restaurant
from apps.menus.models import MenuCategory
from apps.qrcodes.models import QRCode


def public_menu(request, restaurant_slug, qr_slug=None):
    """
    /m/<slug>/           → browse-only menu (no ordering)
    /m/<slug>/<qr-slug>/ → redirect to ordering page with cart
    """
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, is_active=True)

    if qr_slug:
        qr = QRCode.objects.filter(restaurant=restaurant, slug=qr_slug).first()
        if qr:
            # Track scan
            qr.scan_count  += 1
            qr.last_scanned = timezone.now()
            qr.save(update_fields=["scan_count", "last_scanned"])
        # Redirect to the full ordering page
        from django.urls import reverse
        return redirect(
            reverse("place_order",
                    kwargs={"restaurant_slug": restaurant_slug,
                            "qr_slug": qr_slug})
        )

    # No QR slug — plain browse menu (no order buttons)
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
''')

# ══════════════════════════════════════════════════════════════
# 2. Fix orders/views.py — make place_order handle missing QR
# ══════════════════════════════════════════════════════════════

write('apps/orders/views.py', '''import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from apps.restaurants.models import Restaurant
from apps.menus.models import MenuCategory, MenuItem
from apps.qrcodes.models import QRCode
from .models import Order, OrderItem


def place_order(request, restaurant_slug, qr_slug):
    """Customer ordering page — shown after scanning QR code."""
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, is_active=True)
    qr         = QRCode.objects.filter(restaurant=restaurant, slug=qr_slug).first()

    # If QR not found redirect to browse menu
    if not qr:
        from django.urls import reverse
        return redirect(reverse("public_menu", kwargs={"restaurant_slug": restaurant_slug}))

    categories = MenuCategory.objects.filter(
        restaurant=restaurant
    ).prefetch_related("items")

    if request.method == "POST":
        try:
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
            customer_name = customer_name,
            notes         = notes,
            status        = "pending",
        )

        for item_data in items_data:
            try:
                menu_item = MenuItem.objects.get(
                    pk=item_data["id"],
                    category__restaurant=restaurant,
                    is_available=True
                )
            except MenuItem.DoesNotExist:
                continue
            qty = max(1, int(item_data.get("qty", 1)))
            OrderItem.objects.create(
                order     = order,
                menu_item = menu_item,
                name      = menu_item.name,
                price     = menu_item.price,
                quantity  = qty,
            )

        return JsonResponse({
            "success":  True,
            "order_id": order.pk,
            "total":    float(order.get_total()),
        })

    return render(request, "orders/place_order.html", {
        "restaurant": restaurant,
        "categories": categories,
        "qr":         qr,
    })


def order_confirm(request, order_id):
    """Confirmation page shown to customer after placing order."""
    order = get_object_or_404(Order, pk=order_id)
    return render(request, "orders/order_confirm.html", {"order": order})
''')

# ══════════════════════════════════════════════════════════════
# 3. Beautiful place_order.html with Add to Cart buttons
# ══════════════════════════════════════════════════════════════

write('templates/orders/place_order.html', """{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Order — {{ restaurant.name }}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --brand: {{ restaurant.theme_color }};
      --font-d: 'Playfair Display', Georgia, serif;
      --font-b: 'DM Sans', sans-serif;
    }
    *, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
    html { scroll-behavior:smooth; }
    body { font-family:var(--font-b); background:#F8F7F4;
           color:#1A1A1A; padding-bottom:100px; }

    /* ── HEADER ─────────────────────────────────── */
    .header {
      background: var(--brand);
      padding: 1.5rem 1rem 2.5rem;
      text-align: center;
      position: relative; overflow: hidden;
    }
    .header::before {
      content:''; position:absolute; inset:0;
      background:radial-gradient(ellipse 80% 60% at 50% 0%,
                 rgba(255,255,255,0.15) 0%, transparent 70%);
    }
    .header::after {
      content:''; position:absolute; bottom:-2px;
      left:0; right:0; height:28px;
      background:#F8F7F4;
      clip-path:ellipse(55% 100% at 50% 100%);
    }
    .header-logo {
      width:64px; height:64px; border-radius:50%;
      object-fit:cover; border:2px solid rgba(255,255,255,0.4);
      margin:0 auto 0.6rem; display:block; position:relative;
    }
    .header-logo-ph {
      width:56px; height:56px; border-radius:50%;
      background:rgba(255,255,255,0.2);
      display:flex; align-items:center; justify-content:center;
      font-size:1.6rem; margin:0 auto 0.6rem; position:relative;
    }
    .header-name {
      font-family:var(--font-d); font-size:1.6rem; font-weight:700;
      color:#fff; position:relative;
    }
    .header-table {
      font-size:0.82rem; color:rgba(255,255,255,0.8);
      margin-top:0.3rem; position:relative;
    }

    /* ── CATEGORY TABS ───────────────────────────── */
    .tabs {
      position:sticky; top:0; z-index:50; background:#fff;
      box-shadow:0 2px 10px rgba(0,0,0,0.08);
      overflow-x:auto; -webkit-overflow-scrolling:touch;
    }
    .tabs::-webkit-scrollbar { display:none; }
    .tabs-inner {
      display:flex; padding:0 0.5rem;
      white-space:nowrap; min-width:max-content;
    }
    .tab {
      padding:0.8rem 1rem; font-size:0.875rem; font-weight:500;
      color:#888; border-bottom:3px solid transparent;
      cursor:pointer; text-decoration:none; transition:all 0.2s;
    }
    .tab:hover { color:var(--brand); }
    .tab.active { color:var(--brand); border-bottom-color:var(--brand); font-weight:600; }

    /* ── MENU BODY ───────────────────────────────── */
    .menu-body { padding:0 0.75rem; }
    .section { padding:1.25rem 0 0.25rem; }
    .section-header {
      display:flex; align-items:center; gap:0.6rem; margin-bottom:0.85rem;
    }
    .section-title { font-family:var(--font-d); font-size:1.2rem; font-weight:700; }
    .section-line { flex:1; height:1px;
                    background:linear-gradient(90deg,var(--brand),transparent);
                    opacity:0.25; }
    .section-count { font-size:0.72rem; color:#bbb; background:#f0f0f0;
                     padding:0.12rem 0.45rem; border-radius:100px; }

    /* ── ITEM CARD ───────────────────────────────── */
    .item-card {
      background:#fff; border-radius:14px; margin-bottom:0.65rem;
      display:flex; overflow:hidden;
      box-shadow:0 1px 6px rgba(0,0,0,0.06);
      border:2px solid transparent;
      transition:all 0.2s;
    }
    .item-card.in-cart { border-color:var(--brand); }
    .item-img {
      width:90px; flex-shrink:0;
      object-fit:cover; display:block;
    }
    .item-img-ph {
      width:90px; flex-shrink:0;
      background:linear-gradient(135deg,#F8F7F4,#EDE9E3);
      display:flex; align-items:center;
      justify-content:center; font-size:1.6rem;
    }
    .item-body { padding:0.75rem; flex:1; display:flex;
                 flex-direction:column; justify-content:space-between; }
    .item-name { font-weight:600; font-size:0.9rem; color:#1A1A1A; line-height:1.3; }
    .item-desc { font-size:0.75rem; color:#999; margin-top:0.25rem;
                 line-height:1.4;
                 display:-webkit-box; -webkit-line-clamp:2;
                 -webkit-box-orient:vertical; overflow:hidden; }
    .item-badges { display:flex; gap:0.3rem; margin-top:0.2rem; flex-wrap:wrap; }
    .badge-popular { background:#FEF9C3; color:#854D0E;
                     font-size:0.65rem; font-weight:700;
                     padding:0.12rem 0.4rem; border-radius:4px; }
    .item-footer {
      display:flex; align-items:center;
      justify-content:space-between; margin-top:0.6rem;
    }
    .item-price {
      font-family:var(--font-d); font-size:1rem;
      font-weight:700; color:var(--brand);
    }

    /* ── ADD / QTY CONTROL ───────────────────────── */
    .add-btn {
      background:var(--brand); color:#fff;
      border:none; border-radius:8px;
      padding:0.4rem 0.85rem; font-size:0.82rem; font-weight:700;
      cursor:pointer; transition:all 0.2s;
      display:flex; align-items:center; gap:0.3rem;
      font-family:var(--font-b);
    }
    .add-btn:hover { opacity:0.88; transform:scale(1.04); }

    .qty-ctrl {
      display:none;
      align-items:center; gap:0.4rem;
    }
    .qty-ctrl.visible { display:flex; }
    .qty-btn {
      width:30px; height:30px; border-radius:50%;
      background:var(--brand); color:#fff;
      border:none; font-size:1.1rem; font-weight:700;
      cursor:pointer; display:flex; align-items:center;
      justify-content:center; transition:opacity 0.2s;
      font-family:var(--font-b);
    }
    .qty-btn:active { opacity:0.7; }
    .qty-num { font-weight:700; font-size:0.95rem;
               min-width:20px; text-align:center; color:#1A1A1A; }

    /* ── STICKY CART BAR ─────────────────────────── */
    .cart-bar {
      position:fixed; bottom:0; left:0; right:0; z-index:100;
      background:var(--brand); color:#fff;
      padding:0.9rem 1.25rem;
      display:flex; align-items:center; justify-content:space-between;
      box-shadow:0 -4px 20px rgba(0,0,0,0.15);
      transform:translateY(100%);
      transition:transform 0.3s cubic-bezier(0.4,0,0.2,1);
    }
    .cart-bar.visible { transform:translateY(0); }
    .cart-info-label { font-size:0.8rem; opacity:0.85; }
    .cart-info-total { font-size:1.05rem; font-weight:700; }
    .cart-btn {
      background:#fff; color:var(--brand);
      border:none; border-radius:100px;
      padding:0.6rem 1.4rem; font-weight:700; font-size:0.9rem;
      cursor:pointer; white-space:nowrap; font-family:var(--font-b);
    }
    .cart-count-badge {
      background:rgba(255,255,255,0.25);
      border-radius:100px; padding:0.1rem 0.5rem;
      font-size:0.8rem; font-weight:700; margin-left:0.3rem;
    }

    /* ── ORDER MODAL ─────────────────────────────── */
    .overlay {
      position:fixed; inset:0; background:rgba(0,0,0,0.5);
      z-index:200; display:flex; align-items:flex-end;
      justify-content:center; opacity:0; pointer-events:none;
      transition:opacity 0.25s;
    }
    .overlay.open { opacity:1; pointer-events:all; }
    .modal {
      background:#fff; border-radius:24px 24px 0 0;
      padding:1.5rem; width:100%; max-width:520px;
      max-height:85vh; overflow-y:auto;
      transform:translateY(100%);
      transition:transform 0.3s cubic-bezier(0.4,0,0.2,1);
    }
    .overlay.open .modal { transform:translateY(0); }
    .modal-handle {
      width:40px; height:4px; background:#E0E0E0;
      border-radius:2px; margin:0 auto 1.25rem;
    }
    .modal-title { font-family:var(--font-d); font-size:1.2rem;
                   font-weight:700; margin-bottom:1rem; }
    .order-row {
      display:flex; justify-content:space-between; align-items:center;
      padding:0.5rem 0; border-bottom:1px solid #F5F5F5;
      font-size:0.875rem;
    }
    .order-row-name { color:#333; }
    .order-row-price { color:var(--brand); font-weight:600; }
    .order-total-row {
      display:flex; justify-content:space-between;
      padding:0.75rem 0 0; font-weight:700; font-size:1rem;
      border-top:2px solid #F0F0F0; margin-top:0.5rem;
    }
    .modal input, .modal textarea {
      width:100%; padding:0.65rem 0.9rem;
      border:1.5px solid #E0E0E0; border-radius:10px;
      font-size:0.9rem; margin-bottom:0.75rem;
      font-family:var(--font-b); outline:none; color:#333;
      transition:border-color 0.2s;
    }
    .modal input:focus, .modal textarea:focus {
      border-color:var(--brand);
    }
    .modal textarea { resize:none; }
    .place-order-btn {
      width:100%; background:var(--brand); color:#fff;
      border:none; border-radius:14px; padding:1rem;
      font-weight:700; font-size:1rem; cursor:pointer;
      margin-top:0.25rem; font-family:var(--font-b);
      transition:opacity 0.2s;
    }
    .place-order-btn:disabled { opacity:0.6; cursor:not-allowed; }
    .cancel-txt {
      display:block; text-align:center;
      margin-top:0.85rem; color:#999; font-size:0.85rem;
      cursor:pointer; padding:0.25rem;
    }
    .divider { height:1px; background:#F0F0F0; margin:1rem 0; }
  </style>
</head>
<body>

<!-- Header -->
<div class="header">
  {% if restaurant.logo %}
    <img src="{{ restaurant.logo.url }}" alt="{{ restaurant.name }}" class="header-logo">
  {% else %}
    <div class="header-logo-ph">🍽</div>
  {% endif %}
  <h1 class="header-name">{{ restaurant.name }}</h1>
  <p class="header-table">📍 {{ qr.label }} &nbsp;·&nbsp; Tap + to add items</p>
</div>

<!-- Category Tabs -->
<div class="tabs">
  <div class="tabs-inner">
    {% for cat in categories %}
      <a href="#sec-{{ cat.pk }}" class="tab" data-cat="{{ cat.pk }}">
        {{ cat.name }}
      </a>
    {% endfor %}
  </div>
</div>

<!-- Menu -->
<div class="menu-body">
  {% for cat in categories %}
  <div class="section" id="sec-{{ cat.pk }}">
    <div class="section-header">
      <h2 class="section-title">{{ cat.name }}</h2>
      <div class="section-line"></div>
      <span class="section-count">{{ cat.items.count }}</span>
    </div>

    {% for item in cat.items.all %}
      {% if item.is_available %}
      <div class="item-card" id="card-{{ item.pk }}"
           data-id="{{ item.pk }}"
           data-name="{{ item.name }}"
           data-price="{{ item.price }}">

        {% if item.image %}
          <img src="{{ item.image.url }}" alt="{{ item.name }}" class="item-img">
        {% else %}
          <div class="item-img-ph">🍴</div>
        {% endif %}

        <div class="item-body">
          <div>
            <div class="item-name">{{ item.name }}</div>
            <div class="item-badges">
              {% if item.is_popular %}
                <span class="badge-popular">⭐ Popular</span>
              {% endif %}
            </div>
            {% if item.description %}
              <div class="item-desc">{{ item.description }}</div>
            {% endif %}
          </div>
          <div class="item-footer">
            <div class="item-price">₹{{ item.price }}</div>
            <!-- ADD button -->
            <button class="add-btn" id="add-{{ item.pk }}"
                    onclick="addItem({{ item.pk }})">
              + Add
            </button>
            <!-- QTY control (hidden until added) -->
            <div class="qty-ctrl" id="qty-{{ item.pk }}">
              <button class="qty-btn" onclick="changeQty({{ item.pk }}, -1)">−</button>
              <span class="qty-num" id="qnum-{{ item.pk }}">1</span>
              <button class="qty-btn" onclick="changeQty({{ item.pk }}, +1)">+</button>
            </div>
          </div>
        </div>
      </div>
      {% endif %}
    {% endfor %}
  </div>
  {% endfor %}
</div>

<!-- Sticky Cart Bar -->
<div class="cart-bar" id="cartBar">
  <div>
    <div class="cart-info-label">
      Your order
      <span class="cart-count-badge" id="cartCount">0</span>
    </div>
    <div class="cart-info-total" id="cartTotal">₹0.00</div>
  </div>
  <button class="cart-btn" onclick="openModal()">
    Review Order →
  </button>
</div>

<!-- Order Modal -->
<div class="overlay" id="overlay">
  <div class="modal">
    <div class="modal-handle"></div>
    <div class="modal-title">Review Your Order</div>

    <!-- Order items list -->
    <div id="orderList"></div>
    <div class="order-total-row">
      <span>Total</span>
      <span id="modalTotal">₹0.00</span>
    </div>

    <div class="divider"></div>

    <!-- Customer details -->
    <input type="text" id="custName"
           placeholder="Your name (optional)">
    <textarea id="custNotes" rows="2"
              placeholder="Special instructions — e.g. no onions, extra spicy..."></textarea>

    <!-- Place order -->
    <button class="place-order-btn" id="placeBtn" onclick="submitOrder()">
      ✓ Place Order
    </button>
    <span class="cancel-txt" onclick="closeModal()">Cancel</span>
  </div>
</div>

<script>
  const cart = {};   // { id: { name, price, qty } }
  const CSRF = '{{ csrf_token }}';
  const ORDER_URL   = "{% url 'place_order' restaurant.slug qr.slug %}";
  const CONFIRM_URL = "/orders/confirm/";

  // ── Add item (first tap) ──────────────────────────
  function addItem(id) {
    const card  = document.getElementById('card-' + id);
    const name  = card.dataset.name;
    const price = parseFloat(card.dataset.price);

    cart[id] = { name, price, qty: 1 };

    document.getElementById('add-' + id).style.display  = 'none';
    document.getElementById('qty-' + id).classList.add('visible');
    document.getElementById('qnum-' + id).textContent   = 1;
    card.classList.add('in-cart');

    updateCartBar();
  }

  // ── Change quantity ───────────────────────────────
  function changeQty(id, delta) {
    if (!cart[id]) return;
    cart[id].qty += delta;

    if (cart[id].qty <= 0) {
      delete cart[id];
      document.getElementById('add-' + id).style.display = '';
      document.getElementById('qty-' + id).classList.remove('visible');
      document.getElementById('card-' + id).classList.remove('in-cart');
    } else {
      document.getElementById('qnum-' + id).textContent = cart[id].qty;
    }
    updateCartBar();
  }

  // ── Update sticky bar ─────────────────────────────
  function updateCartBar() {
    const items = Object.entries(cart);
    const count = items.reduce((s, [, v]) => s + v.qty, 0);
    const total = items.reduce((s, [, v]) => s + v.price * v.qty, 0);

    document.getElementById('cartCount').textContent = count;
    document.getElementById('cartTotal').textContent = '₹' + total.toFixed(2);
    document.getElementById('cartBar')
            .classList.toggle('visible', count > 0);
  }

  // ── Open modal ────────────────────────────────────
  function openModal() {
    const items = Object.entries(cart);
    let html = '', total = 0;

    items.forEach(([id, v]) => {
      const sub = v.price * v.qty;
      total += sub;
      html += `<div class="order-row">
        <span class="order-row-name">${v.qty} × ${v.name}</span>
        <span class="order-row-price">₹${sub.toFixed(2)}</span>
      </div>`;
    });

    document.getElementById('orderList').innerHTML   = html;
    document.getElementById('modalTotal').textContent = '₹' + total.toFixed(2);
    document.getElementById('overlay').classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    document.getElementById('overlay').classList.remove('open');
    document.body.style.overflow = '';
  }

  // Close overlay by tapping background
  document.getElementById('overlay').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
  });

  // ── Submit order ──────────────────────────────────
  async function submitOrder() {
    const items = Object.entries(cart).map(([id, v]) => ({ id, qty: v.qty }));
    if (!items.length) return;

    const btn = document.getElementById('placeBtn');
    btn.textContent = 'Placing order...';
    btn.disabled    = true;

    try {
      const resp = await fetch(ORDER_URL, {
        method:  'POST',
        headers: {
          'Content-Type':  'application/json',
          'X-CSRFToken':   CSRF,
        },
        body: JSON.stringify({
          items,
          customer_name: document.getElementById('custName').value.trim(),
          notes:         document.getElementById('custNotes').value.trim(),
        }),
      });

      const data = await resp.json();

      if (data.success) {
        window.location.href = CONFIRM_URL + data.order_id + '/';
      } else {
        alert(data.error || 'Something went wrong. Please try again.');
        btn.textContent = '✓ Place Order';
        btn.disabled    = false;
      }
    } catch (err) {
      alert('Network error. Please check your connection.');
      btn.textContent = '✓ Place Order';
      btn.disabled    = false;
    }
  }

  // ── Tab highlight on scroll ───────────────────────
  const sections = document.querySelectorAll('.section[id]');
  const tabs     = document.querySelectorAll('.tab');

  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const id = e.target.id.replace('sec-', '');
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
        const top = target.getBoundingClientRect().top + window.scrollY - 56;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });
</script>
</body>
</html>
""")

print("\n" + "=" * 60)
print("ALL DONE!")
print("=" * 60)
print("""
Restart server:
  python manage.py runserver

Test the full flow:
  1. Go to:  http://127.0.0.1:8000/qr/
  2. Click "Download PNG" on any QR code
  3. Scan the downloaded PNG with your phone
     OR visit directly:
     http://127.0.0.1:8000/orders/place/<restaurant-slug>/<qr-slug>/

  What you will see:
  - Beautiful menu with restaurant branding
  - Each item has a "+ Add" button
  - Tapping "+ Add" shows qty controls (− 1 +)
  - Sticky cart bar appears at bottom with total
  - "Review Order →" opens a modal with order summary
  - Enter name + special instructions (optional)
  - "Place Order" sends to kitchen and shows confirmation

Deploy:
  git add .
  git commit -m "Fix ordering flow - add to cart buttons"
  git push origin main
""")

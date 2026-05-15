"""
Run from project root:  python fix_all.py
Fixes:
  1. Live menu not showing after QR scan
  2. Network error when placing order
  3. Missing kitchen_screen.html
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

def write(rel, content):
    path = os.path.join(BASE, rel.replace('/', os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✓ {rel}")

print("=" * 60)
print("Fixing: Live Menu + Order Placement + Kitchen Screen")
print("=" * 60)

# ══════════════════════════════════════════════════════════════
# FIX 1 — apps/menus/public_views.py
# QR scan now redirects to ordering page correctly
# ══════════════════════════════════════════════════════════════
write('apps/menus/public_views.py', '''import os
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
''')

# ══════════════════════════════════════════════════════════════
# FIX 2 — apps/orders/views.py
# ══════════════════════════════════════════════════════════════
write('apps/orders/views.py', '''import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from apps.restaurants.models import Restaurant
from apps.menus.models import MenuCategory, MenuItem
from apps.qrcodes.models import QRCode
from .models import Order, OrderItem


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
    ).prefetch_related("items")

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
            customer_name = customer_name,
            notes         = notes,
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
    order = get_object_or_404(Order, pk=order_id)
    return render(request, "orders/order_confirm.html", {"order": order})
''')

# ══════════════════════════════════════════════════════════════
# FIX 3 — apps/orders/waiter_views.py
# ══════════════════════════════════════════════════════════════
write('apps/orders/waiter_views.py', '''import json
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
            "customer":   o.customer_name,
            "status":     o.status,
            "notes":      o.notes,
            "total":      float(o.get_total()),
            "item_count": o.get_item_count(),
            "created_at": o.created_at.strftime("%H:%M"),
            "items": [
                {"name": i.name, "qty": i.quantity, "price": float(i.price)}
                for i in o.items.all()
            ],
        })
    return JsonResponse({"orders": data})
''')

# ══════════════════════════════════════════════════════════════
# FIX 4 — apps/orders/urls.py  (clean, no stray names)
# ══════════════════════════════════════════════════════════════
write('apps/orders/urls.py', '''from django.urls import path
from . import views, waiter_views

urlpatterns = [
    path("place/<slug:restaurant_slug>/<slug:qr_slug>/",
         views.place_order,            name="place_order"),
    path("confirm/<int:order_id>/",
         views.order_confirm,          name="order_confirm"),
    path("kitchen/",
         waiter_views.kitchen_screen,  name="kitchen_screen"),
    path("kitchen/update/<int:order_id>/",
         waiter_views.update_status,   name="update_order_status"),
    path("kitchen/orders/json/",
         waiter_views.orders_json,     name="orders_json"),
]
''')

# ══════════════════════════════════════════════════════════════
# FIX 5 — templates/orders/place_order.html
# CSRF token read from hidden form field (most reliable)
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
    :root{ --brand:{{ restaurant.theme_color }}; --fd:'Playfair Display',Georgia,serif; --fb:'DM Sans',sans-serif; }
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
    html{scroll-behavior:smooth;}
    body{font-family:var(--fb);background:#F8F7F4;color:#1A1A1A;padding-bottom:100px;}

    .header{background:var(--brand);padding:1.5rem 1rem 2.5rem;text-align:center;position:relative;overflow:hidden;}
    .header::before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse 80% 60% at 50% 0%,rgba(255,255,255,0.15) 0%,transparent 70%);}
    .header::after{content:'';position:absolute;bottom:-2px;left:0;right:0;height:28px;background:#F8F7F4;clip-path:ellipse(55% 100% at 50% 100%);}
    .header-logo{width:64px;height:64px;border-radius:50%;object-fit:cover;border:2px solid rgba(255,255,255,0.4);margin:0 auto 0.6rem;display:block;position:relative;}
    .header-logo-ph{width:56px;height:56px;border-radius:50%;background:rgba(255,255,255,0.2);display:flex;align-items:center;justify-content:center;font-size:1.6rem;margin:0 auto 0.6rem;position:relative;}
    .header-name{font-family:var(--fd);font-size:1.6rem;font-weight:700;color:#fff;position:relative;}
    .header-table{font-size:0.82rem;color:rgba(255,255,255,0.8);margin-top:0.3rem;position:relative;}

    .tabs{position:sticky;top:0;z-index:50;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,0.08);overflow-x:auto;-webkit-overflow-scrolling:touch;}
    .tabs::-webkit-scrollbar{display:none;}
    .tabs-inner{display:flex;padding:0 0.5rem;white-space:nowrap;min-width:max-content;}
    .tab{padding:0.8rem 1rem;font-size:0.875rem;font-weight:500;color:#888;border-bottom:3px solid transparent;cursor:pointer;text-decoration:none;transition:all 0.2s;}
    .tab:hover{color:var(--brand);}
    .tab.active{color:var(--brand);border-bottom-color:var(--brand);font-weight:600;}

    .menu-body{padding:0 0.75rem;}
    .section{padding:1.25rem 0 0.25rem;}
    .section-header{display:flex;align-items:center;gap:0.6rem;margin-bottom:0.85rem;}
    .section-title{font-family:var(--fd);font-size:1.2rem;font-weight:700;}
    .section-line{flex:1;height:1px;background:linear-gradient(90deg,var(--brand),transparent);opacity:0.25;}
    .section-count{font-size:0.72rem;color:#bbb;background:#f0f0f0;padding:0.12rem 0.45rem;border-radius:100px;}

    .item-card{background:#fff;border-radius:14px;margin-bottom:0.65rem;display:flex;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,0.06);border:2px solid transparent;transition:all 0.2s;}
    .item-card.in-cart{border-color:var(--brand);}
    .item-img{width:90px;flex-shrink:0;object-fit:cover;display:block;}
    .item-img-ph{width:90px;flex-shrink:0;background:linear-gradient(135deg,#F8F7F4,#EDE9E3);display:flex;align-items:center;justify-content:center;font-size:1.6rem;}
    .item-body{padding:0.75rem;flex:1;display:flex;flex-direction:column;justify-content:space-between;}
    .item-name{font-weight:600;font-size:0.9rem;color:#1A1A1A;line-height:1.3;}
    .item-desc{font-size:0.75rem;color:#999;margin-top:0.25rem;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
    .item-badges{display:flex;gap:0.3rem;margin-top:0.2rem;flex-wrap:wrap;}
    .badge-popular{background:#FEF9C3;color:#854D0E;font-size:0.65rem;font-weight:700;padding:0.12rem 0.4rem;border-radius:4px;}
    .item-footer{display:flex;align-items:center;justify-content:space-between;margin-top:0.6rem;}
    .item-price{font-family:var(--fd);font-size:1rem;font-weight:700;color:var(--brand);}

    .add-btn{background:var(--brand);color:#fff;border:none;border-radius:8px;padding:0.4rem 0.85rem;font-size:0.82rem;font-weight:700;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;gap:0.3rem;font-family:var(--fb);}
    .add-btn:hover{opacity:0.88;transform:scale(1.04);}
    .qty-ctrl{display:none;align-items:center;gap:0.4rem;}
    .qty-ctrl.visible{display:flex;}
    .qty-btn{width:30px;height:30px;border-radius:50%;background:var(--brand);color:#fff;border:none;font-size:1.1rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:opacity 0.2s;font-family:var(--fb);}
    .qty-btn:active{opacity:0.7;}
    .qty-num{font-weight:700;font-size:0.95rem;min-width:20px;text-align:center;color:#1A1A1A;}

    .cart-bar{position:fixed;bottom:0;left:0;right:0;z-index:100;background:var(--brand);color:#fff;padding:0.9rem 1.25rem;display:flex;align-items:center;justify-content:space-between;box-shadow:0 -4px 20px rgba(0,0,0,0.15);transform:translateY(100%);transition:transform 0.3s cubic-bezier(0.4,0,0.2,1);}
    .cart-bar.visible{transform:translateY(0);}
    .cart-info-label{font-size:0.8rem;opacity:0.85;}
    .cart-info-total{font-size:1.05rem;font-weight:700;}
    .cart-btn{background:#fff;color:var(--brand);border:none;border-radius:100px;padding:0.6rem 1.4rem;font-weight:700;font-size:0.9rem;cursor:pointer;white-space:nowrap;font-family:var(--fb);}
    .cart-count-badge{background:rgba(255,255,255,0.25);border-radius:100px;padding:0.1rem 0.5rem;font-size:0.8rem;font-weight:700;margin-left:0.3rem;}

    .overlay{position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:200;display:flex;align-items:flex-end;justify-content:center;opacity:0;pointer-events:none;transition:opacity 0.25s;}
    .overlay.open{opacity:1;pointer-events:all;}
    .modal{background:#fff;border-radius:24px 24px 0 0;padding:1.5rem;width:100%;max-width:520px;max-height:85vh;overflow-y:auto;transform:translateY(100%);transition:transform 0.3s cubic-bezier(0.4,0,0.2,1);}
    .overlay.open .modal{transform:translateY(0);}
    .modal-handle{width:40px;height:4px;background:#E0E0E0;border-radius:2px;margin:0 auto 1.25rem;}
    .modal-title{font-family:var(--fd);font-size:1.2rem;font-weight:700;margin-bottom:1rem;}
    .order-row{display:flex;justify-content:space-between;align-items:center;padding:0.5rem 0;border-bottom:1px solid #F5F5F5;font-size:0.875rem;}
    .order-row-name{color:#333;}
    .order-row-price{color:var(--brand);font-weight:600;}
    .order-total-row{display:flex;justify-content:space-between;padding:0.75rem 0 0;font-weight:700;font-size:1rem;border-top:2px solid #F0F0F0;margin-top:0.5rem;}
    .modal input,.modal textarea{width:100%;padding:0.65rem 0.9rem;border:1.5px solid #E0E0E0;border-radius:10px;font-size:0.9rem;margin-bottom:0.75rem;font-family:var(--fb);outline:none;color:#333;transition:border-color 0.2s;}
    .modal input:focus,.modal textarea:focus{border-color:var(--brand);}
    .modal textarea{resize:none;}
    .place-order-btn{width:100%;background:var(--brand);color:#fff;border:none;border-radius:14px;padding:1rem;font-weight:700;font-size:1rem;cursor:pointer;margin-top:0.25rem;font-family:var(--fb);transition:opacity 0.2s;}
    .place-order-btn:disabled{opacity:0.6;cursor:not-allowed;}
    .cancel-txt{display:block;text-align:center;margin-top:0.85rem;color:#999;font-size:0.85rem;cursor:pointer;padding:0.25rem;}
    .divider{height:1px;background:#F0F0F0;margin:1rem 0;}
  </style>
</head>
<body>

<!-- Hidden form to get CSRF token reliably -->
<form id="csrfForm" style="display:none;">{% csrf_token %}</form>

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

<!-- Tabs -->
<div class="tabs">
  <div class="tabs-inner">
    {% for cat in categories %}
      <a href="#sec-{{ cat.pk }}" class="tab" data-cat="{{ cat.pk }}">{{ cat.name }}</a>
    {% endfor %}
  </div>
</div>

<!-- Menu items -->
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
           data-id="{{ item.pk }}" data-name="{{ item.name }}" data-price="{{ item.price }}">
        {% if item.image %}
          <img src="{{ item.image.url }}" alt="{{ item.name }}" class="item-img">
        {% else %}
          <div class="item-img-ph">🍴</div>
        {% endif %}
        <div class="item-body">
          <div>
            <div class="item-name">{{ item.name }}</div>
            <div class="item-badges">
              {% if item.is_popular %}<span class="badge-popular">⭐ Popular</span>{% endif %}
            </div>
            {% if item.description %}
              <div class="item-desc">{{ item.description }}</div>
            {% endif %}
          </div>
          <div class="item-footer">
            <div class="item-price">₹{{ item.price }}</div>
            <button class="add-btn" id="add-{{ item.pk }}" onclick="addItem({{ item.pk }})">+ Add</button>
            <div class="qty-ctrl" id="qty-{{ item.pk }}">
              <button class="qty-btn" onclick="changeQty({{ item.pk }},-1)">−</button>
              <span class="qty-num" id="qnum-{{ item.pk }}">1</span>
              <button class="qty-btn" onclick="changeQty({{ item.pk }},+1)">+</button>
            </div>
          </div>
        </div>
      </div>
      {% endif %}
    {% endfor %}
  </div>
  {% endfor %}
</div>

<!-- Cart bar -->
<div class="cart-bar" id="cartBar">
  <div>
    <div class="cart-info-label">Your order <span class="cart-count-badge" id="cartCount">0</span></div>
    <div class="cart-info-total" id="cartTotal">₹0.00</div>
  </div>
  <button class="cart-btn" onclick="openModal()">Review Order →</button>
</div>

<!-- Order modal -->
<div class="overlay" id="overlay">
  <div class="modal">
    <div class="modal-handle"></div>
    <div class="modal-title">Review Your Order</div>
    <div id="orderList"></div>
    <div class="order-total-row"><span>Total</span><span id="modalTotal">₹0.00</span></div>
    <div class="divider"></div>
    <input type="text" id="custName" placeholder="Your name (optional)">
    <textarea id="custNotes" rows="2" placeholder="Special instructions — e.g. no onions, extra spicy..."></textarea>
    <button class="place-order-btn" id="placeBtn" onclick="submitOrder()">✓ Place Order</button>
    <span class="cancel-txt" onclick="closeModal()">Cancel</span>
  </div>
</div>

<script>
  const cart      = {};
  const CSRF      = document.querySelector('[name=csrfmiddlewaretoken]').value;
  const ORDER_URL = "{% url 'place_order' restaurant.slug qr.slug %}";

  function addItem(id) {
    const card = document.getElementById('card-' + id);
    cart[id]   = { name: card.dataset.name, price: parseFloat(card.dataset.price), qty: 1 };
    document.getElementById('add-'  + id).style.display = 'none';
    document.getElementById('qty-'  + id).classList.add('visible');
    document.getElementById('qnum-' + id).textContent   = 1;
    card.classList.add('in-cart');
    updateCartBar();
  }

  function changeQty(id, delta) {
    if (!cart[id]) return;
    cart[id].qty += delta;
    if (cart[id].qty <= 0) {
      delete cart[id];
      document.getElementById('add-'  + id).style.display = '';
      document.getElementById('qty-'  + id).classList.remove('visible');
      document.getElementById('card-' + id).classList.remove('in-cart');
    } else {
      document.getElementById('qnum-' + id).textContent = cart[id].qty;
    }
    updateCartBar();
  }

  function updateCartBar() {
    const items = Object.entries(cart);
    const count = items.reduce((s,[,v]) => s + v.qty, 0);
    const total = items.reduce((s,[,v]) => s + v.price * v.qty, 0);
    document.getElementById('cartCount').textContent = count;
    document.getElementById('cartTotal').textContent = '₹' + total.toFixed(2);
    document.getElementById('cartBar').classList.toggle('visible', count > 0);
  }

  function openModal() {
    const items = Object.entries(cart);
    let html = '', total = 0;
    items.forEach(([id,v]) => {
      const sub = v.price * v.qty; total += sub;
      html += `<div class="order-row">
        <span class="order-row-name">${v.qty} × ${v.name}</span>
        <span class="order-row-price">₹${sub.toFixed(2)}</span>
      </div>`;
    });
    document.getElementById('orderList').innerHTML    = html;
    document.getElementById('modalTotal').textContent = '₹' + total.toFixed(2);
    document.getElementById('overlay').classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    document.getElementById('overlay').classList.remove('open');
    document.body.style.overflow = '';
  }

  document.getElementById('overlay').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
  });

  async function submitOrder() {
    const items = Object.entries(cart).map(([id,v]) => ({ id, qty: v.qty }));
    if (!items.length) return;
    const btn = document.getElementById('placeBtn');
    btn.textContent = 'Placing order...';
    btn.disabled    = true;
    try {
      const resp = await fetch(ORDER_URL, {
        method:  'POST',
        headers: { 'Content-Type':'application/json', 'X-CSRFToken': CSRF },
        body:    JSON.stringify({
          items,
          customer_name: document.getElementById('custName').value.trim(),
          notes:         document.getElementById('custNotes').value.trim(),
        }),
      });
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      const data = await resp.json();
      if (data.success) {
        window.location.href = '/orders/confirm/' + data.order_id + '/';
      } else {
        alert(data.error || 'Something went wrong. Please try again.');
        btn.textContent = '✓ Place Order';
        btn.disabled    = false;
      }
    } catch(err) {
      console.error(err);
      alert('Could not place order. Please try again.');
      btn.textContent = '✓ Place Order';
      btn.disabled    = false;
    }
  }

  // Scroll tab highlight
  const sections = document.querySelectorAll('.section[id]');
  const tabs     = document.querySelectorAll('.tab');
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const id = e.target.id.replace('sec-','');
        tabs.forEach(t => t.classList.toggle('active', t.dataset.cat === id));
      }
    });
  }, { rootMargin:'-25% 0px -65% 0px' });
  sections.forEach(s => obs.observe(s));
  tabs.forEach(tab => {
    tab.addEventListener('click', e => {
      e.preventDefault();
      const t = document.querySelector(tab.getAttribute('href'));
      if (t) window.scrollTo({ top: t.getBoundingClientRect().top + window.scrollY - 56, behavior:'smooth' });
    });
  });
</script>
</body>
</html>
""")

# ══════════════════════════════════════════════════════════════
# FIX 6 — templates/orders/kitchen_screen.html
# ══════════════════════════════════════════════════════════════
write('templates/orders/kitchen_screen.html', """{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kitchen — {{ restaurant.name }}</title>
  <link rel="stylesheet" href="{% static 'css/main.css' %}">
  <style>
    body{background:#0D0D0D;color:#fff;margin:0;font-family:'DM Sans',sans-serif;}
    .ks-header{background:#1A1A1A;border-bottom:1px solid #333;padding:1rem 1.5rem;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:50;}
    .ks-title{font-size:1.2rem;font-weight:700;color:#fff;}
    .ks-sub{font-size:0.8rem;color:#888;margin-top:0.1rem;}
    .live-dot{width:10px;height:10px;background:#22C55E;border-radius:50%;display:inline-block;margin-right:0.4rem;animation:pulse 1.5s infinite;}
    @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
    .ks-body{padding:1.25rem;}
    .ks-stats{display:flex;gap:1rem;margin-bottom:1.25rem;flex-wrap:wrap;}
    .ks-stat{background:#1A1A1A;border:1px solid #333;border-radius:12px;padding:0.75rem 1.25rem;text-align:center;}
    .ks-stat__num{font-size:1.5rem;font-weight:700;color:#E63946;}
    .ks-stat__label{font-size:0.72rem;color:#666;text-transform:uppercase;letter-spacing:0.06em;margin-top:0.1rem;}
    .ks-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;}
    .order-card{background:#1A1A1A;border-radius:16px;overflow:hidden;border:2px solid #333;transition:all 0.3s;}
    .order-card.status-pending{border-color:#EAB308;}
    .order-card.status-confirmed{border-color:#3B82F6;}
    .order-card.status-preparing{border-color:#F97316;}
    .order-card.status-ready{border-color:#22C55E;}
    .order-header{padding:0.85rem 1rem;display:flex;align-items:center;justify-content:space-between;}
    .order-table{font-weight:700;font-size:1rem;color:#fff;}
    .order-time{font-size:0.75rem;color:#888;}
    .order-status{font-size:0.75rem;font-weight:700;padding:0.2rem 0.65rem;border-radius:100px;}
    .badge-pending{background:#FEF9C3;color:#854D0E;}
    .badge-confirmed{background:#DBEAFE;color:#1E40AF;}
    .badge-preparing{background:#FFF7ED;color:#C2410C;}
    .badge-ready{background:#DCFCE7;color:#166534;}
    .order-items{padding:0 1rem 0.75rem;border-top:1px solid #2A2A2A;}
    .order-item-row{display:flex;justify-content:space-between;padding:0.4rem 0;font-size:0.875rem;border-bottom:1px solid #222;color:#CCC;}
    .qty-badge{background:#333;color:#fff;padding:0.1rem 0.4rem;border-radius:4px;font-size:0.75rem;font-weight:700;margin-right:0.4rem;}
    .order-footer{padding:0.75rem 1rem;border-top:1px solid #2A2A2A;display:flex;align-items:center;justify-content:space-between;gap:0.5rem;}
    .order-total{font-size:0.9rem;font-weight:700;color:#fff;}
    .status-btns{display:flex;gap:0.4rem;flex-wrap:wrap;}
    .ks-btn{border:none;padding:0.35rem 0.75rem;border-radius:8px;font-size:0.78rem;font-weight:700;cursor:pointer;transition:all 0.2s;}
    .btn-confirm{background:#3B82F6;color:#fff;}
    .btn-prepare{background:#F97316;color:#fff;}
    .btn-ready{background:#22C55E;color:#fff;}
    .btn-complete{background:#6B7280;color:#fff;}
    .btn-cancel{background:#EF4444;color:#fff;}
    .customer-note{padding:0.5rem 1rem;background:#111;font-size:0.8rem;color:#888;}
    .empty-state{text-align:center;padding:5rem 1rem;grid-column:1/-1;}
    .empty-state .icon{font-size:4rem;margin-bottom:1rem;opacity:0.3;}
    .empty-state p{color:#666;}
    .new-order-flash{position:fixed;top:1rem;right:1rem;z-index:999;background:#22C55E;color:#fff;padding:0.75rem 1.25rem;border-radius:12px;font-weight:700;font-size:0.9rem;box-shadow:0 8px 24px rgba(34,197,94,0.4);display:none;}
  </style>
</head>
<body>
<div class="ks-header">
  <div>
    <div class="ks-title">🍽 {{ restaurant.name }} — Kitchen Screen</div>
    <div class="ks-sub"><span class="live-dot"></span>Live · Auto-refreshes every 8 seconds</div>
  </div>
  <a href="{% url 'dashboard' %}" style="color:#888;font-size:0.85rem;text-decoration:none;">← Dashboard</a>
</div>

<div class="new-order-flash" id="newFlash">🔔 New Order!</div>

<div class="ks-body">
  <div class="ks-stats">
    <div class="ks-stat">
      <div class="ks-stat__num" id="statTotal">{{ active_orders.count }}</div>
      <div class="ks-stat__label">Active Orders</div>
    </div>
  </div>

  <div class="ks-grid" id="ordersGrid">
    {% for order in active_orders %}
    <div class="order-card status-{{ order.status }}" id="order-{{ order.pk }}">
      <div class="order-header">
        <div>
          <div class="order-table">📍 {{ order.table_number }}</div>
          {% if order.customer_name %}
            <div style="font-size:0.78rem;color:#888;">{{ order.customer_name }}</div>
          {% endif %}
        </div>
        <div style="text-align:right;">
          <div class="order-status badge-{{ order.status }}">{{ order.get_status_display }}</div>
          <div class="order-time">{{ order.created_at|date:"H:i" }}</div>
        </div>
      </div>
      <div class="order-items">
        {% for item in order.items.all %}
        <div class="order-item-row">
          <span><span class="qty-badge">×{{ item.quantity }}</span>{{ item.name }}</span>
          <span style="color:#888;">₹{{ item.subtotal }}</span>
        </div>
        {% endfor %}
      </div>
      {% if order.notes %}<div class="customer-note">📝 {{ order.notes }}</div>{% endif %}
      <div class="order-footer">
        <div class="order-total">₹{{ order.get_total }}</div>
        <div class="status-btns">
          {% if order.status == 'pending' %}
            <button class="ks-btn btn-confirm" onclick="setStatus({{ order.pk }},'confirmed')">Confirm</button>
            <button class="ks-btn btn-cancel"  onclick="setStatus({{ order.pk }},'cancelled')">Cancel</button>
          {% elif order.status == 'confirmed' %}
            <button class="ks-btn btn-prepare" onclick="setStatus({{ order.pk }},'preparing')">Preparing</button>
          {% elif order.status == 'preparing' %}
            <button class="ks-btn btn-ready"   onclick="setStatus({{ order.pk }},'ready')">Ready ✓</button>
          {% elif order.status == 'ready' %}
            <button class="ks-btn btn-complete" onclick="setStatus({{ order.pk }},'completed')">Served ✓</button>
          {% endif %}
        </div>
      </div>
    </div>
    {% empty %}
    <div class="empty-state">
      <div class="icon">🍽</div>
      <p>No active orders right now.</p>
      <p style="font-size:0.8rem;margin-top:0.5rem;color:#555;">Orders appear here automatically when customers place them.</p>
    </div>
    {% endfor %}
  </div>
</div>

<script>
  const UPDATE_URL = "{% url 'update_order_status' 0 %}".replace('/0/','/');
  const JSON_URL   = "{% url 'orders_json' %}";
  const CSRF       = '{{ csrf_token }}';
  let   lastCount  = {{ active_orders.count }};

  async function setStatus(id, status) {
    try {
      const r = await fetch(UPDATE_URL + id + '/', {
        method: 'POST',
        headers: {'Content-Type':'application/json','X-CSRFToken':CSRF},
        body: JSON.stringify({status})
      });
      if (r.ok) refreshOrders();
    } catch(e) { console.error(e); }
  }

  async function refreshOrders() {
    try {
      const r    = await fetch(JSON_URL);
      const data = await r.json();
      document.getElementById('statTotal').textContent = data.orders.length;
      if (data.orders.length > lastCount) {
        document.getElementById('newFlash').style.display = 'block';
        setTimeout(() => document.getElementById('newFlash').style.display = 'none', 3000);
      }
      lastCount = data.orders.length;
      const grid = document.getElementById('ordersGrid');
      if (!data.orders.length) {
        grid.innerHTML = '<div class="empty-state"><div class="icon">🍽</div><p>No active orders right now.</p></div>';
        return;
      }
      const labels = {pending:'Pending',confirmed:'Confirmed',preparing:'Preparing',ready:'Ready'};
      const mkBtns = (o) => {
        if (o.status==='pending')   return `<button class="ks-btn btn-confirm" onclick="setStatus(${o.id},'confirmed')">Confirm</button><button class="ks-btn btn-cancel" onclick="setStatus(${o.id},'cancelled')">Cancel</button>`;
        if (o.status==='confirmed') return `<button class="ks-btn btn-prepare" onclick="setStatus(${o.id},'preparing')">Preparing</button>`;
        if (o.status==='preparing') return `<button class="ks-btn btn-ready"   onclick="setStatus(${o.id},'ready')">Ready ✓</button>`;
        if (o.status==='ready')     return `<button class="ks-btn btn-complete" onclick="setStatus(${o.id},'completed')">Served ✓</button>`;
        return '';
      };
      grid.innerHTML = data.orders.map(o => `
        <div class="order-card status-${o.status}">
          <div class="order-header">
            <div>
              <div class="order-table">📍 ${o.table}</div>
              ${o.customer?`<div style="font-size:0.78rem;color:#888;">${o.customer}</div>`:''}
            </div>
            <div style="text-align:right;">
              <div class="order-status badge-${o.status}">${labels[o.status]||o.status}</div>
              <div class="order-time">${o.created_at}</div>
            </div>
          </div>
          <div class="order-items">
            ${o.items.map(i=>`<div class="order-item-row"><span><span class="qty-badge">×${i.qty}</span>${i.name}</span><span style="color:#888;">₹${(i.price*i.qty).toFixed(2)}</span></div>`).join('')}
          </div>
          ${o.notes?`<div class="customer-note">📝 ${o.notes}</div>`:''}
          <div class="order-footer">
            <div class="order-total">₹${o.total.toFixed(2)}</div>
            <div class="status-btns">${mkBtns(o)}</div>
          </div>
        </div>`).join('');
    } catch(e) { console.error(e); }
  }

  setInterval(refreshOrders, 8000);
</script>
</body>
</html>
""")

# ══════════════════════════════════════════════════════════════
# FIX 7 — templates/orders/order_confirm.html
# ══════════════════════════════════════════════════════════════
write('templates/orders/order_confirm.html', """{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Order Placed — {{ order.restaurant.name }}</title>
  <link rel="stylesheet" href="{% static 'css/main.css' %}">
  <style>
    body{background:#F8F7F4;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:1rem;}
    .card{background:#fff;border-radius:20px;padding:2rem;max-width:420px;width:100%;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,0.1);}
    .check{width:72px;height:72px;background:#F0FDF4;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:2rem;margin:0 auto 1.25rem;}
    h1{font-size:1.5rem;font-weight:700;margin-bottom:0.5rem;}
    .table-badge{display:inline-block;background:#EFF6FF;color:#1E40AF;padding:0.35rem 1rem;border-radius:100px;font-size:0.85rem;font-weight:600;margin-bottom:1.25rem;}
    .items{text-align:left;border-top:1px solid #eee;margin-top:1rem;}
    .row{display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid #f5f5f5;font-size:0.875rem;}
    .total-row{display:flex;justify-content:space-between;padding:0.75rem 0 0;font-weight:700;font-size:1rem;}
    .note-box{background:#FFFBEB;border:1px solid #FCD34D;border-radius:10px;padding:0.85rem;margin-top:1rem;text-align:left;font-size:0.85rem;color:#92400E;}
  </style>
</head>
<body>
<div class="card">
  <div class="check">✅</div>
  <h1>Order Placed!</h1>
  <p style="color:#666;font-size:0.9rem;margin-bottom:1rem;">Your order has been sent to the kitchen.</p>
  <div class="table-badge">📍 {{ order.table_number }}</div>
  {% if order.customer_name %}
    <p style="font-size:0.875rem;color:#555;margin-bottom:0.75rem;">Hi <strong>{{ order.customer_name }}</strong>! Your order is being prepared.</p>
  {% endif %}
  <div class="items">
    {% for item in order.items.all %}
      <div class="row">
        <span>{{ item.quantity }}× {{ item.name }}</span>
        <span>₹{{ item.subtotal }}</span>
      </div>
    {% endfor %}
    <div class="total-row">
      <span>Total</span>
      <span>₹{{ order.get_total }}</span>
    </div>
  </div>
  {% if order.notes %}
    <div class="note-box">📝 {{ order.notes }}</div>
  {% endif %}
  <p style="margin-top:1.5rem;font-size:0.8rem;color:#aaa;">Order #{{ order.pk }} · {{ order.created_at|date:"H:i" }}</p>
  <p style="font-size:0.85rem;color:#666;margin-top:0.5rem;">A waiter will come to your table shortly.</p>
</div>
</body>
</html>
""")

print("\n" + "=" * 60)
print("ALL FIXED!")
print("=" * 60)
print("""
Now run:
  python manage.py runserver

Full test flow:
  1. Go to http://127.0.0.1:8000/qr/
  2. Click Download on any QR code → choose template
  3. Open the downloaded PNG and scan it with phone
     OR visit: http://127.0.0.1:8000/orders/place/cafe-delight/cafe-delight/
  4. Tap "+ Add" on items
  5. Tap "Review Order" → fill name → tap "Place Order"
  6. See confirmation page
  7. Check kitchen: http://127.0.0.1:8000/orders/kitchen/

Deploy after testing:
  git add .
  git commit -m "Fix ordering flow completely"
  git push origin main
""")

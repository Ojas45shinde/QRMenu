"""
Run this script to set up the complete online ordering system.
Command: python setup_ordering.py
"""
import os
import sys
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
print("=" * 60)
print("QR Menu — Setting Up Online Ordering System")
print("=" * 60)

# ── 1. Create orders app ──────────────────────────────────────────────────────
orders_dir = os.path.join(BASE, 'apps', 'orders')
for d in [orders_dir, os.path.join(orders_dir, 'migrations')]:
    os.makedirs(d, exist_ok=True)

for d in [orders_dir, os.path.join(orders_dir, 'migrations')]:
    init = os.path.join(d, '__init__.py')
    if not os.path.exists(init):
        open(init, 'w').close()

print("✓ apps/orders/ directory created")

# ── 2. models.py ─────────────────────────────────────────────────────────────
models = '''from django.db import models
from apps.restaurants.models import Restaurant
from apps.menus.models import MenuItem


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending",    "Pending"),
        ("confirmed",  "Confirmed"),
        ("preparing",  "Preparing"),
        ("ready",      "Ready"),
        ("completed",  "Completed"),
        ("cancelled",  "Cancelled"),
    ]

    restaurant   = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="orders")
    table_number = models.CharField(max_length=50)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    note         = models.TextField(blank=True, help_text="Special instructions from customer")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — {self.restaurant.name} — Table {self.table_number}"

    def calculate_total(self):
        self.total_amount = sum(item.subtotal for item in self.items.all())
        self.save(update_fields=["total_amount"])

    @property
    def status_color(self):
        return {
            "pending":   "yellow",
            "confirmed": "blue",
            "preparing": "orange",
            "ready":     "green",
            "completed": "gray",
            "cancelled": "red",
        }.get(self.status, "gray")


class OrderItem(models.Model):
    order     = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    name      = models.CharField(max_length=200)   # snapshot at time of order
    price     = models.DecimalField(max_digits=8, decimal_places=2)
    quantity  = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.name}"
'''
with open(os.path.join(orders_dir, 'models.py'), 'w', encoding='utf-8') as f:
    f.write(models)
print("✓ apps/orders/models.py")

# ── 3. views.py ──────────────────────────────────────────────────────────────
views = '''import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils import timezone
from .models import Order, OrderItem
from apps.restaurants.models import Restaurant
from apps.menus.models import MenuCategory


def _restaurant(user):
    try:
        return user.restaurant
    except Exception:
        return None


# ── Customer: Place Order ────────────────────────────────────────────────────
@require_POST
def place_order(request, restaurant_slug):
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, is_active=True)

    try:
        data         = json.loads(request.body)
        items_data   = data.get("items", [])
        table_number = data.get("table_number", "").strip()
        note         = data.get("note", "").strip()

        if not items_data:
            return JsonResponse({"success": False, "error": "Your cart is empty."}, status=400)

        if not table_number:
            return JsonResponse({"success": False, "error": "Table number is required."}, status=400)

        # Create order
        order = Order.objects.create(
            restaurant=restaurant,
            table_number=table_number,
            note=note,
            status="pending",
        )

        # Add items
        from apps.menus.models import MenuItem
        for item_data in items_data:
            menu_item = MenuItem.objects.filter(pk=item_data.get("id")).first()
            if menu_item and menu_item.is_available:
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    name=menu_item.name,
                    price=menu_item.price,
                    quantity=int(item_data.get("quantity", 1)),
                )

        order.calculate_total()

        return JsonResponse({
            "success":      True,
            "order_id":     order.pk,
            "order_number": f"#{order.pk:04d}",
            "total":        str(order.total_amount),
            "table":        order.table_number,
            "items_count":  order.items.count(),
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ── Waiter: Orders Dashboard ─────────────────────────────────────────────────
@login_required
def orders_dashboard(request):
    restaurant = _restaurant(request.user)
    if not restaurant:
        return redirect("restaurant_edit")

    status_filter = request.GET.get("status", "active")

    if status_filter == "active":
        orders = Order.objects.filter(
            restaurant=restaurant
        ).exclude(status__in=["completed", "cancelled"]).prefetch_related("items")
    elif status_filter == "completed":
        orders = Order.objects.filter(
            restaurant=restaurant,
            status="completed"
        ).prefetch_related("items")[:50]
    else:
        orders = Order.objects.filter(
            restaurant=restaurant
        ).prefetch_related("items")[:100]

    return render(request, "orders/dashboard.html", {
        "orders":        orders,
        "status_filter": status_filter,
        "restaurant":    restaurant,
    })


# ── Waiter: Update Order Status ───────────────────────────────────────────────
@login_required
@require_POST
def update_order_status(request, pk):
    restaurant = _restaurant(request.user)
    order      = get_object_or_404(Order, pk=pk, restaurant=restaurant)
    new_status = request.POST.get("status")

    valid = ["pending", "confirmed", "preparing", "ready", "completed", "cancelled"]
    if new_status in valid:
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Order #{order.pk:04d} marked as {new_status}.")

    # HTMX: return just the order card
    if request.headers.get("HX-Request"):
        return render(request, "orders/partials/order_card.html", {"order": order})

    return redirect("orders_dashboard")


# ── HTMX: Poll for new orders (auto-refresh) ─────────────────────────────────
@login_required
def orders_poll(request):
    """Returns active orders HTML for HTMX polling."""
    restaurant = _restaurant(request.user)
    if not restaurant:
        return JsonResponse({})

    orders = Order.objects.filter(
        restaurant=restaurant
    ).exclude(status__in=["completed", "cancelled"]).prefetch_related("items")

    return render(request, "orders/partials/orders_list.html", {"orders": orders})


# ── Customer: Order Status Check ─────────────────────────────────────────────
def order_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return JsonResponse({
        "status":       order.status,
        "status_label": order.get_status_display(),
        "updated_at":   order.updated_at.strftime("%H:%M"),
    })
'''
with open(os.path.join(orders_dir, 'views.py'), 'w', encoding='utf-8') as f:
    f.write(views)
print("✓ apps/orders/views.py")

# ── 4. urls.py ───────────────────────────────────────────────────────────────
urls = '''from django.urls import path
from . import views

urlpatterns = [
    # Customer
    path("place/<slug:restaurant_slug>/",  views.place_order,         name="place_order"),
    path("status/<int:order_id>/",         views.order_status,        name="order_status"),
    # Waiter / Owner
    path("dashboard/",                     views.orders_dashboard,    name="orders_dashboard"),
    path("dashboard/poll/",                views.orders_poll,         name="orders_poll"),
    path("<int:pk>/status/",               views.update_order_status, name="update_order_status"),
]
'''
with open(os.path.join(orders_dir, 'urls.py'), 'w', encoding='utf-8') as f:
    f.write(urls)
print("✓ apps/orders/urls.py")

# ── 5. admin.py ──────────────────────────────────────────────────────────────
admin_py = '''from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model   = OrderItem
    extra   = 0
    readonly_fields = ["name", "price", "quantity", "subtotal"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display   = ["id", "restaurant", "table_number", "status", "total_amount", "created_at"]
    list_filter    = ["status", "restaurant"]
    search_fields  = ["table_number", "restaurant__name"]
    readonly_fields = ["created_at", "updated_at", "total_amount"]
    inlines        = [OrderItemInline]
'''
with open(os.path.join(orders_dir, 'admin.py'), 'w', encoding='utf-8') as f:
    f.write(admin_py)
print("✓ apps/orders/admin.py")

# ── 6. apps.py ───────────────────────────────────────────────────────────────
apps_py = '''from django.apps import AppConfig

class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.orders"
'''
with open(os.path.join(orders_dir, 'apps.py'), 'w', encoding='utf-8') as f:
    f.write(apps_py)
print("✓ apps/orders/apps.py")

# ── 7. Templates ─────────────────────────────────────────────────────────────
tmpl_dir = os.path.join(BASE, 'templates', 'orders')
partials_dir = os.path.join(tmpl_dir, 'partials')
os.makedirs(partials_dir, exist_ok=True)

# Waiter orders dashboard
orders_dashboard_html = """{% extends "base.html" %}
{% block title %}Orders — Live Dashboard{% endblock %}

{% block extra_head %}
<style>
  .order-card { background:#fff; border:1px solid var(--border); border-radius:14px; padding:1.25rem; margin-bottom:1rem; transition:all 0.3s; }
  .order-card:hover { box-shadow:0 8px 24px rgba(0,0,0,0.08); }
  .order-card__header { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem; flex-wrap:wrap; gap:0.5rem; }
  .order-num { font-family:var(--font-display); font-size:1.2rem; font-weight:700; color:var(--dark); }
  .order-table { font-size:0.85rem; color:var(--muted); }
  .order-time { font-size:0.78rem; color:var(--muted); }
  .order-items { border-top:1px solid var(--border); padding-top:0.75rem; margin-top:0.5rem; }
  .order-item-row { display:flex; justify-content:space-between; font-size:0.875rem; padding:0.2rem 0; }
  .order-total { display:flex; justify-content:space-between; font-weight:700; font-size:1rem; border-top:1px solid var(--border); margin-top:0.5rem; padding-top:0.5rem; }
  .order-note { background:#FFFBEA; border:1px solid #FCD34D; border-radius:8px; padding:0.5rem 0.75rem; font-size:0.8rem; color:#92400E; margin-top:0.5rem; }
  .status-actions { display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:0.75rem; }
  .badge-pending  { background:#FEF9C3; color:#854D0E; }
  .badge-confirmed{ background:#DBEAFE; color:#1E40AF; }
  .badge-preparing{ background:#FEF3C7; color:#92400E; }
  .badge-ready    { background:#DCFCE7; color:#166534; }
  .badge-completed{ background:#F1F5F9; color:#475569; }
  .badge-cancelled{ background:#FEE2E2; color:#991B1B; }
  .pulse { animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
  .new-order-alert { background:linear-gradient(135deg,#E63946,#C1121F); color:#fff; border-radius:12px; padding:1rem 1.25rem; margin-bottom:1.5rem; display:none; }
</style>
{% endblock %}

{% block content %}
<div class="page">

  <div class="page-header">
    <div>
      <h1 class="page-header__title">Live Orders</h1>
      <p class="page-header__sub">
        Auto-refreshes every 8 seconds
        <span class="pulse" style="color:var(--brand);">●</span>
      </p>
    </div>
    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
      <a href="?status=active"    class="btn {% if status_filter == 'active' %}btn--primary{% else %}btn--ghost{% endif %} btn--sm">🔴 Active</a>
      <a href="?status=completed" class="btn {% if status_filter == 'completed' %}btn--primary{% else %}btn--ghost{% endif %} btn--sm">✓ Completed</a>
      <a href="?status=all"       class="btn {% if status_filter == 'all' %}btn--primary{% else %}btn--ghost{% endif %} btn--sm">All</a>
      <a href="{% url 'dashboard' %}" class="btn btn--ghost btn--sm">← Dashboard</a>
    </div>
  </div>

  <!-- New order alert (shown by JS when new order arrives) -->
  <div class="new-order-alert" id="new-order-alert">
    🔔 <strong>New order received!</strong> Check the list below.
  </div>

  <!-- Stats -->
  <div class="stats-grid" style="margin-bottom:1.5rem;">
    <div class="stat-card">
      <div class="stat-card__icon">🟡</div>
      <div class="stat-card__value">{{ orders|length }}</div>
      <div class="stat-card__label">{% if status_filter == 'active' %}Active Orders{% else %}Orders Shown{% endif %}</div>
    </div>
    <div class="stat-card">
      <div class="stat-card__icon">🍽</div>
      <div class="stat-card__value" id="total-items">—</div>
      <div class="stat-card__label">Total Items</div>
    </div>
    <div class="stat-card">
      <div class="stat-card__icon">💰</div>
      <div class="stat-card__value" id="total-revenue">—</div>
      <div class="stat-card__label">Total Value</div>
    </div>
  </div>

  <!-- Orders list — HTMX polling target -->
  <div id="orders-container"
       hx-get="{% url 'orders_poll' %}"
       hx-trigger="every 8s"
       hx-swap="innerHTML"
       hx-indicator="#poll-indicator">

    {% include "orders/partials/orders_list.html" %}

  </div>

  <div id="poll-indicator" class="htmx-indicator" style="position:fixed;bottom:1rem;right:1rem;"></div>

</div>

<script>
  let prevCount = {{ orders|length }};

  // Calculate stats on load
  function updateStats() {
    const cards = document.querySelectorAll('.order-card');
    let totalItems = 0, totalRevenue = 0;
    cards.forEach(card => {
      totalItems   += parseInt(card.dataset.items   || 0);
      totalRevenue += parseFloat(card.dataset.total || 0);
    });
    const el1 = document.getElementById('total-items');
    const el2 = document.getElementById('total-revenue');
    if(el1) el1.textContent = totalItems;
    if(el2) el2.textContent = '₹' + totalRevenue.toFixed(2);
  }

  // Alert on new order
  document.addEventListener('htmx:afterSwap', function(e) {
    if(e.target.id === 'orders-container') {
      const newCount = document.querySelectorAll('.order-card').length;
      if(newCount > prevCount) {
        const alert = document.getElementById('new-order-alert');
        if(alert) {
          alert.style.display = 'block';
          // Play beep sound
          try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            osc.connect(ctx.destination);
            osc.frequency.value = 880;
            osc.start(); osc.stop(ctx.currentTime + 0.3);
          } catch(e) {}
          setTimeout(() => { alert.style.display = 'none'; }, 5000);
        }
      }
      prevCount = newCount;
      updateStats();
    }
  });
  updateStats();
</script>
{% endblock %}"""

with open(os.path.join(tmpl_dir, 'dashboard.html'), 'w', encoding='utf-8') as f:
    f.write(orders_dashboard_html)
print("✓ templates/orders/dashboard.html")

# Order card partial
order_card_html = """{% load humanize %}
<div class="order-card"
     id="order-{{ order.pk }}"
     data-items="{{ order.items.count }}"
     data-total="{{ order.total_amount }}">

  <div class="order-card__header">
    <div>
      <div class="order-num">Order #{{ order.pk|stringformat:"04d" }}</div>
      <div class="order-table">📍 Table {{ order.table_number }}</div>
    </div>
    <div style="text-align:right;">
      <span class="badge badge--{{ order.status_color }} badge-{{ order.status }}">
        {{ order.get_status_display }}
      </span>
      <div class="order-time">{{ order.created_at|time:"H:i" }}</div>
    </div>
  </div>

  {% if order.note %}
    <div class="order-note">📝 {{ order.note }}</div>
  {% endif %}

  <div class="order-items">
    {% for item in order.items.all %}
      <div class="order-item-row">
        <span>{{ item.quantity }}× {{ item.name }}</span>
        <span>₹{{ item.subtotal }}</span>
      </div>
    {% endfor %}
    <div class="order-total">
      <span>Total</span>
      <span>₹{{ order.total_amount }}</span>
    </div>
  </div>

  <div class="status-actions">
    {% if order.status == "pending" %}
      <form method="POST" action="{% url 'update_order_status' order.pk %}">
        {% csrf_token %}<input type="hidden" name="status" value="confirmed">
        <button type="submit" class="btn btn--primary btn--sm" hx-post="{% url 'update_order_status' order.pk %}" hx-vals='{"status":"confirmed"}' hx-target="#order-{{ order.pk }}" hx-swap="outerHTML">✓ Confirm</button>
      </form>
      <form method="POST" action="{% url 'update_order_status' order.pk %}">
        {% csrf_token %}<input type="hidden" name="status" value="cancelled">
        <button type="submit" class="btn btn--danger btn--sm">✕ Cancel</button>
      </form>
    {% elif order.status == "confirmed" %}
      <form method="POST" action="{% url 'update_order_status' order.pk %}">
        {% csrf_token %}<input type="hidden" name="status" value="preparing">
        <button type="submit" class="btn btn--primary btn--sm">🍳 Preparing</button>
      </form>
    {% elif order.status == "preparing" %}
      <form method="POST" action="{% url 'update_order_status' order.pk %}">
        {% csrf_token %}<input type="hidden" name="status" value="ready">
        <button type="submit" class="btn btn--success btn--sm">🔔 Ready</button>
      </form>
    {% elif order.status == "ready" %}
      <form method="POST" action="{% url 'update_order_status' order.pk %}">
        {% csrf_token %}<input type="hidden" name="status" value="completed">
        <button type="submit" class="btn btn--ghost btn--sm">✓ Completed</button>
      </form>
    {% endif %}
  </div>

</div>"""

with open(os.path.join(partials_dir, 'order_card.html'), 'w', encoding='utf-8') as f:
    f.write(order_card_html)
print("✓ templates/orders/partials/order_card.html")

# Orders list partial
orders_list_html = """{% if orders %}
  {% for order in orders %}
    {% include "orders/partials/order_card.html" %}
  {% endfor %}
{% else %}
  <div class="empty-state">
    <div class="empty-state__icon">🎉</div>
    <div class="empty-state__title">No active orders</div>
    <p class="empty-state__text">New orders will appear here automatically every 8 seconds.</p>
  </div>
{% endif %}"""

with open(os.path.join(partials_dir, 'orders_list.html'), 'w', encoding='utf-8') as f:
    f.write(orders_list_html)
print("✓ templates/orders/partials/orders_list.html")

# ── 8. Update public menu template ───────────────────────────────────────────
public_menu = r"""{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ restaurant.name }} — Menu</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="{% static 'css/main.css' %}">
  <style>
    :root { --brand: {{ restaurant.theme_color }}; --brand-dark: {{ restaurant.theme_color }}; --brand-light: {{ restaurant.theme_color }}18; }
    .menu-header   { background: var(--brand); }
    .menu-tab:hover,.menu-tab--active { background:var(--brand);color:#fff!important;border-color:var(--brand); }
    .menu-section__title { color:var(--brand);border-color:var(--brand); }
    .menu-card__price    { color:var(--brand); }
    /* Cart */
    .cart-bar { position:fixed;bottom:0;left:0;right:0;background:var(--brand);color:#fff;padding:1rem 1.25rem;display:flex;align-items:center;justify-content:space-between;z-index:200;transform:translateY(100%);transition:transform 0.3s ease;box-shadow:0 -4px 20px rgba(0,0,0,0.15); }
    .cart-bar.visible { transform:translateY(0); }
    .cart-bar__info { font-size:0.9rem; }
    .cart-bar__count { font-weight:700;font-size:1.1rem; }
    .cart-bar__total { font-size:0.85rem;opacity:0.85; }
    .cart-bar__btn { background:#fff;color:var(--brand);border:none;padding:0.6rem 1.4rem;border-radius:100px;font-weight:700;font-size:0.9rem;cursor:pointer; }
    /* Item add button */
    .item-add-btn { background:var(--brand);color:#fff;border:none;width:30px;height:30px;border-radius:50%;font-size:1.2rem;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:0.4rem; }
    .item-qty-ctrl { display:flex;align-items:center;gap:0.5rem;margin-top:0.4rem; }
    .item-qty-btn { background:var(--brand);color:#fff;border:none;width:26px;height:26px;border-radius:50%;font-size:1rem;cursor:pointer;display:flex;align-items:center;justify-content:center; }
    .item-qty-num { font-weight:700;font-size:0.95rem;min-width:20px;text-align:center; }
    /* Cart modal */
    .cart-overlay { position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:300;display:none; }
    .cart-modal { position:fixed;bottom:0;left:0;right:0;background:#fff;border-radius:20px 20px 0 0;z-index:400;max-height:85vh;overflow-y:auto;padding:1.5rem;display:none; }
    .cart-modal.open,.cart-overlay.open { display:block; }
    /* Order confirmation */
    .confirm-overlay { position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:500;display:none;align-items:center;justify-content:center; }
    .confirm-overlay.open { display:flex; }
    .confirm-box { background:#fff;border-radius:20px;padding:2rem;max-width:360px;width:90%;text-align:center; }
    .confirm-icon { font-size:3rem;margin-bottom:1rem; }
  </style>
</head>
<body style="background:#F8F7F4;padding-bottom:5rem;">

  <!-- Header -->
  <div class="menu-header">
    {% if restaurant.logo %}
      <img src="{{ restaurant.logo.url }}" class="menu-header__logo" alt="{{ restaurant.name }}">
    {% else %}
      <div style="width:72px;height:72px;border-radius:50%;background:rgba(255,255,255,0.2);display:flex;align-items:center;justify-content:center;font-size:2rem;margin:0 auto 0.75rem;">🍽</div>
    {% endif %}
    <h1 class="menu-header__name">{{ restaurant.name }}</h1>
    {% if restaurant.description %}
      <p class="menu-header__desc">{{ restaurant.description }}</p>
    {% endif %}
  </div>

  <!-- Category tabs -->
  {% if categories %}
  <div class="menu-tabs">
    <div class="menu-tabs__inner">
      {% for cat in categories %}
        <a href="#cat-{{ cat.pk }}" class="menu-tab">{{ cat.name }}</a>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  <!-- Menu sections -->
  {% for cat in categories %}
    <div class="menu-section" id="cat-{{ cat.pk }}">
      <h2 class="menu-section__title">{{ cat.name }}</h2>
      {% for item in cat.items.all %}
        {% if item.is_available %}
        <div class="menu-card" id="item-card-{{ item.pk }}">
          {% if item.image %}<img src="{{ item.image.url }}" class="menu-card__img" alt="{{ item.name }}">{% endif %}
          <div class="menu-card__body">
            <div class="menu-card__top">
              <span class="menu-card__name">{{ item.name }}</span>
              {% if item.is_popular %}<span class="menu-card__popular">⭐ Popular</span>{% endif %}
            </div>
            {% if item.description %}<p class="menu-card__desc">{{ item.description }}</p>{% endif %}
            <div style="display:flex;justify-content:space-between;align-items:flex-end;">
              <p class="menu-card__price">₹{{ item.price }}</p>
              <!-- Add to cart controls -->
              <div id="ctrl-{{ item.pk }}">
                <button class="item-add-btn"
                        onclick="addToCart({{ item.pk }}, '{{ item.name|escapejs }}', {{ item.price }})"
                        title="Add to order">+</button>
              </div>
            </div>
          </div>
        </div>
        {% endif %}
      {% endfor %}
    </div>
  {% endfor %}

  <!-- Cart bar (bottom) -->
  <div class="cart-bar" id="cart-bar">
    <div class="cart-bar__info">
      <div class="cart-bar__count" id="cart-count">0 items</div>
      <div class="cart-bar__total" id="cart-total">₹0.00</div>
    </div>
    <button class="cart-bar__btn" onclick="openCart()">View Order →</button>
  </div>

  <!-- Cart overlay -->
  <div class="cart-overlay" id="cart-overlay" onclick="closeCart()"></div>

  <!-- Cart modal -->
  <div class="cart-modal" id="cart-modal">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.25rem;">
      <h2 style="font-size:1.2rem;font-family:var(--font-display);">Your Order</h2>
      <button onclick="closeCart()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--muted);">×</button>
    </div>

    <div id="cart-items-list"></div>

    <div style="border-top:1px solid var(--border);margin-top:1rem;padding-top:1rem;">
      <div style="display:flex;justify-content:space-between;font-weight:700;font-size:1.1rem;margin-bottom:1.25rem;">
        <span>Total</span><span id="cart-modal-total">₹0.00</span>
      </div>

      <div style="margin-bottom:1rem;">
        <label style="font-size:0.85rem;font-weight:600;display:block;margin-bottom:0.4rem;">
          Table Number <span style="color:var(--brand)">*</span>
        </label>
        <input type="text" id="table-number" placeholder="e.g. Table 3"
               style="width:100%;padding:0.6rem 0.9rem;border:1.5px solid var(--border);border-radius:8px;font-size:0.9rem;outline:none;"
               onfocus="this.style.borderColor='{{ restaurant.theme_color }}'"
               onblur="this.style.borderColor='var(--border)'">
      </div>

      <div style="margin-bottom:1.25rem;">
        <label style="font-size:0.85rem;font-weight:600;display:block;margin-bottom:0.4rem;">
          Special Instructions (optional)
        </label>
        <textarea id="order-note" placeholder="e.g. No onions, extra spicy..."
                  rows="2"
                  style="width:100%;padding:0.6rem 0.9rem;border:1.5px solid var(--border);border-radius:8px;font-size:0.9rem;resize:none;outline:none;font-family:inherit;"
                  onfocus="this.style.borderColor='{{ restaurant.theme_color }}'"
                  onblur="this.style.borderColor='var(--border)'"></textarea>
      </div>

      <button onclick="placeOrder()"
              id="place-order-btn"
              style="width:100%;background:var(--brand);color:#fff;border:none;padding:0.9rem;border-radius:12px;font-weight:700;font-size:1rem;cursor:pointer;">
        Place Order
      </button>
    </div>
  </div>

  <!-- Order confirmation modal -->
  <div class="confirm-overlay" id="confirm-overlay">
    <div class="confirm-box">
      <div class="confirm-icon">🎉</div>
      <h2 style="font-size:1.4rem;font-family:var(--font-display);margin-bottom:0.5rem;">Order Placed!</h2>
      <p id="confirm-order-num" style="font-size:1rem;font-weight:700;color:var(--brand);margin-bottom:0.5rem;"></p>
      <p id="confirm-details" style="font-size:0.875rem;color:var(--muted);margin-bottom:1.5rem;line-height:1.6;"></p>
      <button onclick="closeConfirm()"
              style="width:100%;background:var(--brand);color:#fff;border:none;padding:0.8rem;border-radius:12px;font-weight:700;font-size:0.95rem;cursor:pointer;">
        Back to Menu
      </button>
    </div>
  </div>

  <script src="{% static 'js/main.js' %}"></script>
  <script>
    // Cart state
    let cart = {};

    function addToCart(id, name, price) {
      if(cart[id]) {
        cart[id].qty += 1;
      } else {
        cart[id] = { id, name, price: parseFloat(price), qty: 1 };
      }
      updateCartUI();
      updateItemCtrl(id);
    }

    function removeFromCart(id) {
      if(cart[id]) {
        cart[id].qty -= 1;
        if(cart[id].qty <= 0) delete cart[id];
      }
      updateCartUI();
      updateItemCtrl(id);
    }

    function updateItemCtrl(id) {
      const ctrl = document.getElementById('ctrl-' + id);
      if(!ctrl) return;
      const item = cart[id];
      if(!item || item.qty === 0) {
        ctrl.innerHTML = '<button class="item-add-btn" onclick="addToCart('+id+', \''+encodeURIComponent(ctrl.dataset.name||'')+'\', '+ctrl.dataset.price+')" title="Add">+</button>';
        // Re-set after replace
        const btn = ctrl.querySelector('button');
        if(btn) {
          const card = ctrl.closest('.menu-card');
          const nameEl = card ? card.querySelector('.menu-card__name') : null;
          const priceEl = card ? card.querySelector('.menu-card__price') : null;
          const name = nameEl ? nameEl.textContent.trim() : '';
          const price = priceEl ? priceEl.textContent.replace('₹','').trim() : '0';
          btn.onclick = () => addToCart(id, name, parseFloat(price));
        }
      } else {
        ctrl.innerHTML = '<div class="item-qty-ctrl"><button class="item-qty-btn" onclick="removeFromCart('+id+')">−</button><span class="item-qty-num">'+item.qty+'</span><button class="item-qty-btn" onclick="addToCart('+id+', \''+item.name.replace(/'/g,"\\'")+'\', '+item.price+')">+</button></div>';
      }
    }

    function cartTotal() {
      return Object.values(cart).reduce((s,i) => s + i.price * i.qty, 0);
    }

    function cartCount() {
      return Object.values(cart).reduce((s,i) => s + i.qty, 0);
    }

    function updateCartUI() {
      const count = cartCount();
      const total = cartTotal();
      document.getElementById('cart-count').textContent = count + ' item' + (count !== 1 ? 's' : '');
      document.getElementById('cart-total').textContent = '₹' + total.toFixed(2);
      document.getElementById('cart-bar').classList.toggle('visible', count > 0);
      renderCartItems();
    }

    function renderCartItems() {
      const list = document.getElementById('cart-items-list');
      if(!list) return;
      const items = Object.values(cart);
      if(items.length === 0) {
        list.innerHTML = '<p style="text-align:center;color:var(--muted);padding:1rem;">Your cart is empty</p>';
      } else {
        list.innerHTML = items.map(item => `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:0.6rem 0;border-bottom:1px solid var(--border);">
            <div style="flex:1;">
              <div style="font-weight:600;font-size:0.9rem;">${item.name}</div>
              <div style="font-size:0.8rem;color:var(--muted);">₹${item.price.toFixed(2)} each</div>
            </div>
            <div style="display:flex;align-items:center;gap:0.5rem;">
              <button class="item-qty-btn" onclick="removeFromCart(${item.id});renderCartItems();">−</button>
              <span style="font-weight:700;min-width:20px;text-align:center;">${item.qty}</span>
              <button class="item-qty-btn" onclick="addToCart(${item.id},'${item.name.replace(/'/g,"\\'")}',${item.price});renderCartItems();">+</button>
            </div>
            <div style="font-weight:700;font-size:0.9rem;margin-left:1rem;min-width:60px;text-align:right;">₹${(item.price * item.qty).toFixed(2)}</div>
          </div>
        `).join('');
      }
      document.getElementById('cart-modal-total').textContent = '₹' + cartTotal().toFixed(2);
    }

    function openCart()  { document.getElementById('cart-modal').classList.add('open'); document.getElementById('cart-overlay').classList.add('open'); renderCartItems(); }
    function closeCart() { document.getElementById('cart-modal').classList.remove('open'); document.getElementById('cart-overlay').classList.remove('open'); }
    function closeConfirm() { document.getElementById('confirm-overlay').classList.remove('open'); }

    function placeOrder() {
      const table = document.getElementById('table-number').value.trim();
      const note  = document.getElementById('order-note').value.trim();
      const items = Object.values(cart);

      if(items.length === 0) { alert('Add items to your order first!'); return; }
      if(!table) {
        document.getElementById('table-number').focus();
        document.getElementById('table-number').style.borderColor = '#E63946';
        return;
      }

      const btn = document.getElementById('place-order-btn');
      btn.textContent = 'Placing Order...';
      btn.disabled = true;

      fetch("{% url 'place_order' restaurant.slug %}", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({
          items: items.map(i => ({ id: i.id, quantity: i.qty })),
          table_number: table,
          note: note,
        })
      })
      .then(r => r.json())
      .then(data => {
        if(data.success) {
          closeCart();
          // Show confirmation
          document.getElementById('confirm-order-num').textContent = 'Order ' + data.order_number;
          document.getElementById('confirm-details').innerHTML =
            '📍 Table: <strong>' + data.table + '</strong><br>' +
            '🍽 Items: <strong>' + data.items_count + '</strong><br>' +
            '💰 Total: <strong>₹' + data.total + '</strong><br><br>' +
            'Your order has been sent to the kitchen. A waiter will confirm shortly.';
          document.getElementById('confirm-overlay').classList.add('open');
          // Clear cart
          cart = {};
          updateCartUI();
          // Reset controls
          document.querySelectorAll('.item-qty-ctrl').forEach(ctrl => {
            const parent = ctrl.closest('[id^="ctrl-"]');
            if(parent) {
              const id = parent.id.replace('ctrl-','');
              const card = parent.closest('.menu-card');
              const nameEl = card ? card.querySelector('.menu-card__name') : null;
              const priceEl = card ? card.querySelector('.menu-card__price') : null;
              const name = nameEl ? nameEl.textContent.trim() : '';
              const price = priceEl ? priceEl.textContent.replace('₹','').trim() : '0';
              parent.innerHTML = '<button class="item-add-btn" title="Add">+</button>';
              parent.querySelector('button').onclick = () => addToCart(parseInt(id), name, parseFloat(price));
            }
          });
        } else {
          alert('Error: ' + data.error);
          btn.textContent = 'Place Order';
          btn.disabled = false;
        }
      })
      .catch(err => {
        alert('Connection error. Please try again.');
        btn.textContent = 'Place Order';
        btn.disabled = false;
      });
    }

    function getCookie(name) {
      let v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
      return v ? v[2] : null;
    }
  </script>
</body>
</html>"""

tmpl_menu_path = os.path.join(BASE, 'templates', 'menus', 'public_menu.html')
with open(tmpl_menu_path, 'w', encoding='utf-8') as f:
    f.write(public_menu)
print("✓ templates/menus/public_menu.html (updated with cart)")

# ── 9. Update config/urls.py ─────────────────────────────────────────────────
urls_main = """from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/',      admin.site.urls),
    path('',            include('apps.core.urls')),
    path('auth/',       include('django.contrib.auth.urls')),
    path('dashboard/',  include('apps.restaurants.urls')),
    path('menu/',       include('apps.menus.urls')),
    path('qr/',         include('apps.qrcodes.urls')),
    path('orders/',     include('apps.orders.urls')),
    path('m/',          include('apps.menus.public_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
"""
with open(os.path.join(BASE, 'config', 'urls.py'), 'w', encoding='utf-8') as f:
    f.write(urls_main)
print("✓ config/urls.py updated")

# ── 10. Add orders to INSTALLED_APPS in settings ─────────────────────────────
settings_path = os.path.join(BASE, 'config', 'settings.py')
with open(settings_path, 'r', encoding='utf-8') as f:
    settings_content = f.read()

if '"apps.orders"' not in settings_content and "'apps.orders'" not in settings_content:
    settings_content = settings_content.replace(
        '"apps.qrcodes",',
        '"apps.qrcodes",\n    "apps.orders",'
    )
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(settings_content)
    print("✓ apps.orders added to INSTALLED_APPS")
else:
    print("✓ apps.orders already in INSTALLED_APPS")

# ── 11. Add orders link to dashboard ─────────────────────────────────────────
dashboard_path = os.path.join(BASE, 'templates', 'restaurants', 'dashboard.html')
with open(dashboard_path, 'r', encoding='utf-8') as f:
    dash = f.read()

if 'orders_dashboard' not in dash:
    orders_card = """
    <a href="{% url 'orders_dashboard' %}" class="action-card">
      <div class="action-card__icon">🛎</div>
      <div class="action-card__title">Live Orders</div>
      <div class="action-card__desc">View & manage orders</div>
    </a>"""
    dash = dash.replace(
        '<a href="{% url \'restaurant_edit\' %}" class="action-card">',
        orders_card + '\n    <a href="{% url \'restaurant_edit\' %}" class="action-card">'
    )
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(dash)
    print("✓ Orders card added to dashboard")

# ── 12. Run migrations ────────────────────────────────────────────────────────
print("\nRunning makemigrations for orders...")
subprocess.run([sys.executable, 'manage.py', 'makemigrations', 'orders'], cwd=BASE)
print("Running migrate...")
subprocess.run([sys.executable, 'manage.py', 'migrate'], cwd=BASE)

print("\n" + "=" * 60)
print("ONLINE ORDERING SYSTEM READY!")
print("=" * 60)
print("""
Test it now:
  Customer menu:    http://127.0.0.1:8000/m/cafe-delight/
  Waiter dashboard: http://127.0.0.1:8000/orders/dashboard/

Flow:
  1. Customer scans QR code
  2. Browses menu, taps + to add items
  3. Taps "View Order", enters table number
  4. Taps "Place Order" — sees confirmation
  5. Waiter screen auto-refreshes every 8 seconds
  6. Waiter taps Confirm → Preparing → Ready → Completed
""")

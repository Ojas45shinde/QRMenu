import os

# ── Fix dashboard.html ──────────────────────────────────────────────────────
dashboard = """{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<div class="page">

  {% if not restaurant %}
  <div class="empty-state">
    <div class="empty-state__icon">🏪</div>
    <div class="empty-state__title">No restaurant set up yet</div>
    <p class="empty-state__text">Create your restaurant profile to get started.</p>
    <a href="{% url 'restaurant_edit' %}" class="btn btn--primary">+ Set Up My Restaurant</a>
  </div>

  {% else %}
  <div class="page-header">
    <div>
      <h1 class="page-header__title">{{ restaurant.name }}</h1>
      <p class="page-header__sub">
        Public menu:
        <a href="/m/{{ restaurant.slug }}/" target="_blank" style="color:var(--brand);">
          127.0.0.1:8000/m/{{ restaurant.slug }}/
        </a>
      </p>
    </div>
    <a href="{% url 'restaurant_edit' %}" class="btn btn--ghost btn--sm">Settings</a>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-card__icon">🍽</div>
      <div class="stat-card__value">{{ restaurant.categories.count }}</div>
      <div class="stat-card__label">Categories</div>
    </div>
    <div class="stat-card">
      <div class="stat-card__icon">📱</div>
      <div class="stat-card__value">{{ restaurant.qrcodes.count }}</div>
      <div class="stat-card__label">QR Codes</div>
    </div>
  </div>

  <div class="action-grid">
    <a href="{% url 'category_list' %}" class="action-card">
      <div class="action-card__icon">🍽</div>
      <div class="action-card__title">Manage Menu</div>
      <div class="action-card__desc">Add categories and items</div>
    </a>
    <a href="{% url 'qr_list' %}" class="action-card">
      <div class="action-card__icon">📱</div>
      <div class="action-card__title">QR Codes</div>
      <div class="action-card__desc">Generate and download</div>
    </a>
    <a href="{% url 'restaurant_edit' %}" class="action-card">
      <div class="action-card__icon">⚙️</div>
      <div class="action-card__title">Settings</div>
      <div class="action-card__desc">Logo, theme and info</div>
    </a>
    <a href="/m/{{ restaurant.slug }}/" target="_blank" class="action-card">
      <div class="action-card__icon">👁</div>
      <div class="action-card__title">Preview Menu</div>
      <div class="action-card__desc">See customer view</div>
    </a>
  </div>
  {% endif %}

</div>
{% endblock %}"""

# ── Fix restaurant_form.html ────────────────────────────────────────────────
form = """{% extends "base.html" %}
{% block title %}Restaurant Settings{% endblock %}
{% block content %}
<div class="page--narrow">

  <div class="breadcrumb">
    <a href="{% url 'dashboard' %}">Dashboard</a>
    <span class="breadcrumb__sep">›</span>
    <span class="breadcrumb__current">Settings</span>
  </div>

  <form method="POST" action="{% url 'restaurant_edit' %}" enctype="multipart/form-data">
    {% csrf_token %}

    <div class="card mb-3">
      <div class="card__header">
        <h2 style="font-size:1.1rem;">Restaurant Info</h2>
      </div>
      <div class="card__body">
        <div class="form-group">
          <label class="form-label">Restaurant Name</label>
          <input type="text" name="name" class="form-control"
                 placeholder="e.g. Cafe Delight" required
                 value="{{ form.instance.name }}">
        </div>
        <div class="form-group">
          <label class="form-label">Description</label>
          <textarea name="description" class="form-control"
                    rows="3" placeholder="Short description">{{ form.instance.description }}</textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Phone</label>
          <input type="text" name="phone" class="form-control"
                 placeholder="+91 98765 43210"
                 value="{{ form.instance.phone }}">
        </div>
        <div class="form-group">
          <label class="form-label">Address</label>
          <textarea name="address" class="form-control"
                    rows="2" placeholder="Restaurant address">{{ form.instance.address }}</textarea>
        </div>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card__header">
        <h2 style="font-size:1.1rem;">Branding</h2>
      </div>
      <div class="card__body">
        <div class="form-group">
          <label class="form-label">Logo</label>
          <input type="file" name="logo" accept="image/*"
                 class="form-control" style="padding:0.4rem;">
          <div class="form-help">JPG or PNG</div>
        </div>
        <div class="form-group">
          <label class="form-label">Brand Colour</label>
          <div style="display:flex;align-items:center;gap:1rem;">
            <input type="color" name="theme_color" id="colorpick"
                   value="{{ form.instance.theme_color }}"
                   style="width:60px;height:44px;padding:0.2rem;cursor:pointer;border:1px solid var(--border);border-radius:6px;">
            <div id="colorpreview"
                 style="width:44px;height:44px;border-radius:10px;
                        border:1px solid var(--border);
                        background:{{ form.instance.theme_color }};"></div>
            <span class="text-sm text-muted">Menu header colour</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card__header">
        <h2 style="font-size:1.1rem;">Custom HTML Menu (Optional)</h2>
      </div>
      <div class="card__body">
        <div class="alert alert--info mb-3">
          Upload your own .html menu file. Customers will see it when they scan your QR code.
        </div>
        <div class="form-group">
          <label class="form-label">Upload HTML File</label>
          <input type="file" name="custom_menu_html" accept=".html"
                 class="form-control" style="padding:0.4rem;">
          <div class="form-help">Only .html files, max 2MB</div>
        </div>
        <div style="display:flex;align-items:flex-start;gap:0.75rem;
                    background:var(--light);border:1px solid var(--border);
                    border-radius:8px;padding:1rem;">
          <input type="checkbox" name="use_custom_menu" id="use_custom_menu"
                 style="margin-top:3px;width:16px;height:16px;">
          <div>
            <label for="use_custom_menu" class="form-label" style="cursor:pointer;">
              Show my custom HTML menu to customers
            </label>
            <div class="form-help">Uncheck to use the auto-generated menu.</div>
          </div>
        </div>
      </div>
    </div>

    <div style="display:flex;gap:0.75rem;padding-bottom:2rem;">
      <button type="submit" class="btn btn--primary btn--lg">Save Settings</button>
      <a href="{% url 'dashboard' %}" class="btn btn--ghost btn--lg">Cancel</a>
    </div>

  </form>
</div>
<script>
  var cp = document.getElementById('colorpick');
  var cv = document.getElementById('colorpreview');
  if(cp && cv){ cp.addEventListener('input', function(){ cv.style.background = this.value; }); }
</script>
{% endblock %}"""

# ── Write both files ────────────────────────────────────────────────────────
base = r'C:\Users\acer\Desktop\QRmenu\templates\restaurants'

with open(os.path.join(base, 'dashboard.html'), 'w', encoding='utf-8') as f:
    f.write(dashboard)
print("✓ dashboard.html written")

with open(os.path.join(base, 'restaurant_form.html'), 'w', encoding='utf-8') as f:
    f.write(form)
print("✓ restaurant_form.html written")

print("\nAll done! Now restart the server and visit http://127.0.0.1:8000/dashboard/")

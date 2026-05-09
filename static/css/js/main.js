/* ============================================================
   QR MENU SYSTEM — main.js
   Handles: alerts, nav active states, image previews,
            confirm deletes, menu tab scrolling, theme preview
   ============================================================ */

'use strict';

// ── Auto-dismiss flash messages ─────────────────────────────
function initAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '&times;';
        closeBtn.style.cssText = `
      margin-left: auto; background: none; border: none;
      font-size: 1.1rem; cursor: pointer; opacity: 0.6;
      padding: 0 0.25rem; line-height: 1; color: inherit;
    `;
        closeBtn.addEventListener('click', () => dismissAlert(alert));
        alert.style.display = 'flex';
        alert.appendChild(closeBtn);

        // Auto dismiss after 4 seconds
        setTimeout(() => dismissAlert(alert), 4000);
    });
}

function dismissAlert(el) {
    el.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    el.style.opacity = '0';
    el.style.transform = 'translateY(-6px)';
    setTimeout(() => el.remove(), 300);
}

// ── Active nav link highlighting ────────────────────────────
function initNavHighlight() {
    const links = document.querySelectorAll('.navbar__link');
    const path = window.location.pathname;
    links.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== '/' && path.startsWith(href)) {
            link.classList.add('navbar__link--active');
        } else if (href === '/' && path === '/') {
            link.classList.add('navbar__link--active');
        }
    });
}

// ── Image preview on file input ─────────────────────────────
function initImagePreviews() {
    document.querySelectorAll('input[type="file"][accept*="image"]').forEach(input => {
        const previewId = input.dataset.preview;
        const preview = previewId ? document.getElementById(previewId) : null;

        input.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) return;

            // Validate file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                showToast('Image must be under 5MB', 'error');
                this.value = '';
                return;
            }

            if (preview) {
                const reader = new FileReader();
                reader.onload = e => {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }

            // Show filename next to input
            const label = input.closest('.form-group')?.querySelector('.form-label');
            if (label) {
                const existing = label.querySelector('.file-name-tag');
                if (existing) existing.remove();
                const tag = document.createElement('span');
                tag.className = 'file-name-tag';
                tag.style.cssText = 'font-size:0.75rem; color:#888; font-weight:400; margin-left:0.5rem;';
                tag.textContent = file.name;
                label.appendChild(tag);
            }
        });
    });
}

// ── Theme color preview ─────────────────────────────────────
function initThemeColorPreview() {
    const colorInput = document.querySelector('input[type="color"][name="theme_color"]');
    if (!colorInput) return;

    const previewEl = document.getElementById('theme-preview');

    colorInput.addEventListener('input', function () {
        document.documentElement.style.setProperty('--brand', this.value);
        if (previewEl) {
            previewEl.style.background = this.value;
        }
    });
}

// ── Smooth scroll for menu category tabs ────────────────────
function initMenuTabs() {
    const tabs = document.querySelectorAll('.menu-tab');
    if (!tabs.length) return;

    // Highlight tab on scroll
    const sections = document.querySelectorAll('.menu-section[id]');
    if (!sections.length) return;

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.id;
                tabs.forEach(tab => {
                    tab.classList.toggle('menu-tab--active', tab.getAttribute('href') === `#${id}`);
                });
            }
        });
    }, { rootMargin: '-30% 0px -60% 0px' });

    sections.forEach(s => observer.observe(s));

    // Smooth click scroll
    tabs.forEach(tab => {
        tab.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offset = 120; // account for sticky header
                const top = target.getBoundingClientRect().top + window.scrollY - offset;
                window.scrollTo({ top, behavior: 'smooth' });
            }
        });
    });
}

// ── Toast notification ───────────────────────────────────────
function showToast(message, type = 'info') {
    const typeMap = {
        success: { bg: '#F0FDF4', border: '#86EFAC', color: '#166534', icon: '✓' },
        error: { bg: '#FEF2F2', border: '#FCA5A5', color: '#991B1B', icon: '✕' },
        warning: { bg: '#FFFBEB', border: '#FCD34D', color: '#92400E', icon: '!' },
        info: { bg: '#EFF6FF', border: '#93C5FD', color: '#1E40AF', icon: 'ℹ' },
    };
    const style = typeMap[type] || typeMap.info;

    const toast = document.createElement('div');
    toast.style.cssText = `
    position: fixed; bottom: 1.5rem; right: 1.5rem; z-index: 9999;
    background: ${style.bg}; color: ${style.color};
    border: 1px solid ${style.border};
    padding: 0.75rem 1.1rem; border-radius: 10px;
    font-size: 0.875rem; font-family: 'DM Sans', sans-serif;
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    display: flex; align-items: center; gap: 0.5rem;
    animation: slideUp 0.3s ease;
    max-width: 320px;
  `;
    toast.innerHTML = `<span style="font-weight:700">${style.icon}</span> ${message}`;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(8px)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// ── Confirm delete with inline prompt ───────────────────────
function initConfirmForms() {
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', function (e) {
            const msg = this.dataset.confirm || 'Are you sure you want to delete this?';
            if (!confirm(msg)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });
}

// ── Password visibility toggle ───────────────────────────────
function initPasswordToggles() {
    document.querySelectorAll('[data-toggle-password]').forEach(btn => {
        const targetId = btn.dataset.togglePassword;
        const input = document.getElementById(targetId);
        if (!input) return;

        btn.addEventListener('click', function () {
            const isText = input.type === 'text';
            input.type = isText ? 'password' : 'text';
            this.textContent = isText ? '👁' : '🙈';
        });
    });
}

// ── Slug preview (auto-generate from name field) ─────────────
function initSlugPreview() {
    const nameInput = document.querySelector('input[name="name"]');
    const slugHint = document.getElementById('slug-preview');
    if (!nameInput || !slugHint) return;

    nameInput.addEventListener('input', function () {
        const slug = this.value
            .toLowerCase()
            .trim()
            .replace(/[^a-z0-9\s-]/g, '')
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-');
        slugHint.textContent = slug ? `URL: /m/${slug}/` : '';
    });
}

// ── QR code preview (show URL before downloading) ────────────
function initQRPreview() {
    document.querySelectorAll('[data-qr-url]').forEach(el => {
        const url = el.dataset.qrUrl;
        el.addEventListener('mouseenter', function () {
            const tip = document.createElement('div');
            tip.id = 'qr-tip';
            tip.style.cssText = `
        position: absolute; background: #1A1A2E; color: #fff;
        padding: 0.4rem 0.75rem; border-radius: 6px;
        font-size: 0.75rem; white-space: nowrap;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 100; pointer-events: none;
      `;
            tip.textContent = url;
            document.body.appendChild(tip);

            const rect = this.getBoundingClientRect();
            tip.style.top = `${rect.bottom + window.scrollY + 6}px`;
            tip.style.left = `${rect.left + window.scrollX}px`;
        });
        el.addEventListener('mouseleave', () => {
            document.getElementById('qr-tip')?.remove();
        });
    });
}

// ── Character counter for textareas ─────────────────────────
function initCharCounters() {
    document.querySelectorAll('textarea[maxlength]').forEach(ta => {
        const max = parseInt(ta.getAttribute('maxlength'), 10);
        const counter = document.createElement('div');
        counter.style.cssText = 'font-size:0.75rem; color:#888; text-align:right; margin-top:0.25rem;';
        counter.textContent = `0 / ${max}`;
        ta.parentNode.insertBefore(counter, ta.nextSibling);

        ta.addEventListener('input', () => {
            const len = ta.value.length;
            counter.textContent = `${len} / ${max}`;
            counter.style.color = len > max * 0.9 ? '#E63946' : '#888';
        });
    });
}

// ── Add slideUp animation ────────────────────────────────────
const style = document.createElement('style');
style.textContent = `
  @keyframes slideUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }
`;
document.head.appendChild(style);

// ── Init all on DOM ready ────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initAlerts();
    initNavHighlight();
    initImagePreviews();
    initThemeColorPreview();
    initMenuTabs();
    initConfirmForms();
    initPasswordToggles();
    initSlugPreview();
    initQRPreview();
    initCharCounters();
});

// ── Re-init after HTMX swaps ─────────────────────────────────
document.addEventListener('htmx:afterSwap', () => {
    initAlerts();
    initImagePreviews();
    initConfirmForms();
});
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Restaurant(models.Model):
    owner        = models.OneToOneField(User, on_delete=models.CASCADE)
    name         = models.CharField(max_length=200)
    slug         = models.SlugField(unique=True, blank=True)
    description  = models.TextField(blank=True)
    logo         = models.ImageField(upload_to='logos/', blank=True, null=True)
    address      = models.TextField(blank=True)
    phone        = models.CharField(max_length=20, blank=True)
    theme_color  = models.CharField(max_length=7, default='#E63946')
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    # ── Custom HTML menu upload ──────────────────────────────────
    custom_menu_html = models.FileField(
        upload_to='custom_menus/',
        blank=True,
        null=True,
        help_text='Upload your own HTML menu file. If uploaded, this will be shown to customers instead of the auto-generated menu.'
    )
    use_custom_menu = models.BooleanField(
        default=False,
        help_text='Check this to show your uploaded HTML menu to customers.'
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_menu_url(self):
        return f'/m/{self.slug}/'
from django.db import models
from apps.restaurants.models import Restaurant


class QRCode(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="qrcodes"
    )
    label        = models.CharField(max_length=100)  # e.g. "Table 1"
    slug         = models.SlugField()                # auto-set from label
    scan_count   = models.PositiveIntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    last_scanned = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("restaurant", "slug")]

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug:
            self.slug = slugify(self.label)
        super().save(*args, **kwargs)

    def get_scan_url(self):
        return f"/m/{self.restaurant.slug}/{self.slug}/"

    def __str__(self):
        return f"{self.restaurant.name} — {self.label}"
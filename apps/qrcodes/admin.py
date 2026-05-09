from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import QRCode


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ["label","restaurant","scan_count","last_scanned"]
    readonly_fields = ["scan_count","last_scanned"]
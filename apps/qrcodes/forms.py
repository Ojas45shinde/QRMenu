from django import forms
from .models import QRCode


class QRCodeForm(forms.ModelForm):
    class Meta:
        model  = QRCode
        fields = ["label"]
        widgets = {
            "label": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Table 1, Table 2, Bar Counter, Takeaway"
            }),
        }
        help_texts = {
            "label": "Each label gets its own unique QR code PNG to print.",
        }
from django import forms
from .models import MenuCategory, MenuItem


class MenuCategoryForm(forms.ModelForm):
    class Meta:
        model  = MenuCategory
        fields = ["name", "order"]
        widgets = {
            "name":  forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Starters, Mains, Drinks"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "placeholder": "0"}),
        }


class MenuItemForm(forms.ModelForm):
    class Meta:
        model  = MenuItem
        fields = ["name", "description", "price", "image", "is_available", "is_popular", "order"]
        widgets = {
            "name":        forms.TextInput(attrs={"class": "form-control", "placeholder": "Item name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Brief description (optional)"}),
            "price":       forms.NumberInput(attrs={"class": "form-control", "placeholder": "0.00", "step": "0.01"}),
            "order":       forms.NumberInput(attrs={"class": "form-control", "placeholder": "0"}),
        }
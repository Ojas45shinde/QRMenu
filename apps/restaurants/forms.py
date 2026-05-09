from django import forms
from .models import Restaurant


class RestaurantForm(forms.ModelForm):
    class Meta:
        model  = Restaurant
        fields = [
            'name', 'description', 'logo', 'address', 'phone',
            'theme_color', 'custom_menu_html', 'use_custom_menu'
        ]
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Cafe Delight'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Short description shown on the menu'}),
            'address':     forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Your restaurant address'}),
            'phone':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +91 98765 43210'}),
            'theme_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
        }
        help_texts = {
            'custom_menu_html': 'Upload a .html file. Embed your CSS inside a &lt;style&gt; tag in the HTML file.',
            'use_custom_menu':  'If checked, customers will see your uploaded HTML instead of the auto-generated menu.',
        }

    def clean_custom_menu_html(self):
        f = self.cleaned_data.get('custom_menu_html')
        if f and hasattr(f, 'name'):
            if not f.name.endswith('.html'):
                raise forms.ValidationError('Only .html files are allowed.')
            if f.size > 2 * 1024 * 1024:
                raise forms.ValidationError('File must be under 2MB.')
        return f
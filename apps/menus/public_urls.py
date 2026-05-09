from django.urls import path
from .public_views import public_menu


urlpatterns = [
    # Scanned without table info
    path("<slug:restaurant_slug>/",
         public_menu, name="public_menu"),


    # Scanned from a specific table QR (tracks analytics)
    path("<slug:restaurant_slug>/<slug:qr_slug>/",
         public_menu, name="public_menu_table"),
]
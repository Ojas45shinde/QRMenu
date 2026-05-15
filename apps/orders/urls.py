from django.urls import path
from . import views, waiter_views

urlpatterns = [
    path("place/<slug:restaurant_slug>/<slug:qr_slug>/",
         views.place_order,            name="place_order"),
    path("confirm/<int:order_id>/",
         views.order_confirm,          name="order_confirm"),
    path("kitchen/",
         waiter_views.kitchen_screen,  name="kitchen_screen"),
    path("kitchen/update/<int:order_id>/",
         waiter_views.update_status,   name="update_order_status"),
    path("kitchen/orders/json/",
         waiter_views.orders_json,     name="orders_json"),
]

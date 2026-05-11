from django.urls import path
from . import views

urlpatterns = [
    # Customer
    path("place/<slug:restaurant_slug>/",  views.place_order,         name="place_order"),
    path("status/<int:order_id>/",         views.order_status,        name="order_status"),
    # Waiter / Owner
    path("dashboard/",                     views.orders_dashboard,    name="orders_dashboard"),
    path("dashboard/poll/",                views.orders_poll,         name="orders_poll"),
    path("<int:pk>/status/",               views.update_order_status, name="update_order_status"),
]

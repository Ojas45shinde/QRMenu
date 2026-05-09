from django.urls import path
from . import views


urlpatterns = [
    path("",      views.dashboard,      name="dashboard"),
    path("edit/", views.restaurant_edit, name="restaurant_edit"),
]
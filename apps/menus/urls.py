from django.urls import path
from . import views


urlpatterns = [
    path("categories/",
         views.category_list,   name="category_list"),
    path("categories/new/",
         views.category_create, name="category_create"),
    path("categories/<int:pk>/delete/",
         views.category_delete, name="category_delete"),


    path("categories/<int:cat_pk>/items/",
         views.item_list,   name="item_list"),
    path("categories/<int:cat_pk>/items/new/",
         views.item_create, name="item_create"),
    path("items/<int:pk>/edit/",
         views.item_edit,   name="item_edit"),
    path("items/<int:pk>/delete/",
         views.item_delete, name="item_delete"),
]
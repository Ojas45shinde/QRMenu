from django.urls import path
from . import views
 
urlpatterns = [
    path('',                                views.qr_list,              name='qr_list'),
    path('new/',                            views.qr_create,            name='qr_create'),
    path('<int:pk>/download/',              views.qr_download,          name='qr_download'),
    path('<int:pk>/download/<str:template_key>/', views.qr_download_template, name='qr_download_template'),
    path('<int:pk>/delete/',               views.qr_delete,            name='qr_delete'),
]
 
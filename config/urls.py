from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/',      admin.site.urls),
    path('',            include('apps.core.urls')),
    path('auth/',       include('django.contrib.auth.urls')),
    path('dashboard/',  include('apps.restaurants.urls')),
    path('menu/',       include('apps.menus.urls')),
    path('qr/',         include('apps.qrcodes.urls')),
    path('orders/',     include('apps.orders.urls')),
    path('m/',          include('apps.menus.public_urls')),
    path("",            include("apps.menus.urls")),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

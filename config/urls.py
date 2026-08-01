# ============================================================
# FILE: config/urls.py
# ============================================================
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    #boutiques
    path('api/stores/', include('apps.stores.urls')),
    #syncronisation
    path('api/sync/', include('apps.sync.urls')),
    #abonnements
    path('api/subscriptions/', include('apps.subscriptions.urls')),
]
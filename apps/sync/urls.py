# ============================================================
# FILE: apps/sync/urls.py
# ============================================================
from django.urls import path
from apps.sync.views import SyncPushView, SyncBootstrapView

urlpatterns = [
    path('push/', SyncPushView.as_view(), name='sync-push'),
    path('bootstrap/', SyncBootstrapView.as_view(), name='sync-bootstrap'),
]
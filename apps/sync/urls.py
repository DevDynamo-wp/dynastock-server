# ============================================================
# FILE: apps/sync/urls.py
# ============================================================
from django.urls import path
from apps.sync.views import ActivityLogListView, SyncPushView, SyncBootstrapView

urlpatterns = [
    path('push/', SyncPushView.as_view(), name='sync-push'),
    path('bootstrap/', SyncBootstrapView.as_view(), name='sync-bootstrap'),
    path('activities/', ActivityLogListView.as_view(), name='sync-activities'),
]
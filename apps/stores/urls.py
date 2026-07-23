# ============================================================
# FILE: apps/stores/urls.py
# ============================================================
from django.urls import path
from apps.stores.views import StoreListCreateView

urlpatterns = [
    path('', StoreListCreateView.as_view(), name='store-list-create'),
]
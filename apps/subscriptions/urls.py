# apps/subscriptions/urls.py
# ============================================================
# FILE: apps/subscriptions/urls.py
# ============================================================
from django.urls import path
from apps.subscriptions.views import PlanListView, SubscribeView, MyStatusView

urlpatterns = [
    path('plans/', PlanListView.as_view(), name='subscription-plans'),
    path('subscribe/', SubscribeView.as_view(), name='subscription-subscribe'),
    path('my-status/', MyStatusView.as_view(), name='subscription-my-status'),
]
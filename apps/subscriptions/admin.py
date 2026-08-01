# apps/subscriptions/admin.py
from django.contrib import admin
from apps.subscriptions.models import SubscriptionPlan, Subscription

admin.site.register(SubscriptionPlan)
admin.site.register(Subscription)
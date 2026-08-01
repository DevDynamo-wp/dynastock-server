# apps/subscriptions/serializers.py
# ============================================================
# FILE: apps/subscriptions/serializers.py
# ============================================================
#
# SubscriptionPlanSerializer
# ---------------------------
# Représentation publique d'un plan, pour l'écran "choisir un
# abonnement" côté Flutter.
#
# SubscriptionStatusSerializer
# ------------------------------
# Sérialise le dataclass SubscriptionStatus (Phase 2), pas un
# modèle Django — d'où l'usage de champs simples plutôt que
# ModelSerializer.
# ------------------------------------------------------
from rest_framework import serializers
from apps.subscriptions.models import SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'billing_period', 'price', 'duration_days']


class SubscriptionStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    is_read_only = serializers.BooleanField()
    end_date = serializers.DateTimeField(allow_null=True)
    days_remaining = serializers.IntegerField()
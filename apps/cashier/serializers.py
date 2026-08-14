# ============================================================
# FILE: apps/cashier/serializers.py
# ============================================================
from rest_framework import serializers

from apps.cashier.models import CashSession


class CashSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashSession
        fields = [
            'id', 'store', 'status',
            'opened_by', 'opening_amount', 'opened_at',
            'closed_by', 'closing_amount', 'expected_amount', 'difference', 'closed_at',
        ]
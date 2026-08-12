# ============================================================
# FILE: apps/expenses/serializers.py
# ============================================================
from rest_framework import serializers

from apps.expenses.models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'store', 'category', 'description', 'amount', 'expense_date', 'created_at']
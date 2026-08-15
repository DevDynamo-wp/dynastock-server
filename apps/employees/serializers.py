# ============================================================
# FILE: apps/employees/serializers.py
# ============================================================
from rest_framework import serializers

from apps.employees.models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    linked_member_name = serializers.CharField(
        source='linked_member.user.full_name', read_only=True, allow_null=True
    )

    class Meta:
        model = Employee
        fields = ['id', 'store', 'name', 'phone', 'position', 'hire_date',
                  'salary', 'is_active', 'linked_member', 'linked_member_name', 'created_at']
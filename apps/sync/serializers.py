# ============================================================
# FILE: apps/sync/serializers.py
# ============================================================
#
# OperationInputSerializer
# ------------------------
# Une seule opération du journal, telle qu'envoyée par Flutter.
#
# PushSerializer
# --------------
# Le body complet : un lot (batch) d'opérations envoyées en une
# seule requête, pour limiter le nombre d'appels réseau.
# ------------------------------------------------------
from rest_framework import serializers
from apps.sync.models import JournalOperation


class OperationInputSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    store_id = serializers.UUIDField()
    device_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    operation_type = serializers.ChoiceField(choices=JournalOperation.OperationType.choices)
    entity_type = serializers.CharField()
    entity_id = serializers.CharField()
    payload = serializers.JSONField()
    client_created_at = serializers.DateTimeField()


class PushSerializer(serializers.Serializer):
    operations = OperationInputSerializer(many=True)
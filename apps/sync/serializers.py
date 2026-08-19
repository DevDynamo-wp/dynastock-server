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
from apps.catalog.models import Customer, Supplier, Product, Category
from apps.employees.models import Employee


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



class ActivityLogSerializer(serializers.ModelSerializer):
    """Une entrée du fil d'activité (écran 'Activités récentes' et
    sa page détaillée). Réutilise directement JournalOperation : pas
    de nouveau modèle, chaque action de l'app y est déjà journalisée
    avec son auteur (user), peu importe le type (création,
    modification, suppression).
    """
    author_name = serializers.CharField(source='user.full_name', read_only=True)
    label = serializers.SerializerMethodField()
    # Réutilise le label humain déjà défini sur OperationType.choices
    # (ex: "Créer un client") plutôt que de dupliquer cette traduction
    # côté Flutter.
    action_label = serializers.CharField(
        source='get_operation_type_display', read_only=True
    )

    class Meta:
        model = JournalOperation
        fields = [
            'id', 'store', 'operation_type', 'action_label', 'entity_type',
            'entity_id', 'label', 'author_name', 'client_created_at',
        ]
        read_only_fields = fields

    def get_label(self, obj: JournalOperation) -> str:
        """Nom lisible de l'entité concernée (ex: 'Jean Dupont' pour
        un client). Priorité :
        1. l'entité existe encore -> on lit son nom ACTUEL (le plus
           fiable, fonctionne même après plusieurs modifications) ;
        2. sinon (entité supprimée depuis) -> on retombe sur le nom
           tel qu'il était dans le payload au moment de l'action ;
        3. sinon -> libellé générique avec le type d'entité.
        """
        current_name = self._current_entity_name(obj)
        if current_name:
            return current_name

        payload_name = obj.payload.get('name') if isinstance(obj.payload, dict) else None
        if payload_name:
            return payload_name

        return dict(JournalOperation.OperationType.choices).get(
            obj.operation_type, obj.entity_type
        )

    @staticmethod
    def _current_entity_name(obj: JournalOperation) -> str | None:
        # Import local pour éviter tout risque d'import circulaire
        # entre apps.sync et apps.catalog.

        model_by_entity_type = {
            'customer': Customer,
            'supplier': Supplier,
            'employee': Employee,
            'product': Product,
            'category': Category,
        }
        model = model_by_entity_type.get(obj.entity_type)
        if model is None:
            return None
        try:
            instance = model.objects.get(id=obj.entity_id)
        except model.DoesNotExist:
            return None
        # Employee peut ne pas avoir de champ 'name' direct selon ton
        # implémentation (souvent first_name/last_name) : on tente
        # 'name' d'abord, sinon on assemble.
        if hasattr(instance, 'name'):
            return instance.name
        if hasattr(instance, 'full_name'):
            return instance.full_name
        return None
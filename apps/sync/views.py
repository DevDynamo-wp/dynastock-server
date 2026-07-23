# ============================================================
# FILE: sync/views.py
# ============================================================
#
# SyncPushView
# ------------
# POST /api/sync/push/  → reçoit un lot d'opérations et les
# applique une par une, de façon idempotente.
#
# SyncBootstrapView
# ------------------
# GET /api/sync/bootstrap/  → renvoie tout ce dont Flutter a besoin
# pour reconstruire sa base locale après une réinstallation.
# Pour l'instant : uniquement les boutiques. La clé "stores" restera
# stable ; on ajoutera de nouvelles clés (products, customers...)
# au fil des prochaines phases, sans jamais casser ce qui existe.
# ------------------------------------------------------
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.stores.models import Store, UserStore
from apps.stores.serializers import StoreSerializer
from apps.sync.models import JournalOperation
from apps.sync.serializers import PushSerializer


class SyncPushView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PushSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        results = [
            self._process_operation(request.user, op)
            for op in serializer.validated_data['operations']
        ]
        return Response({'results': results}, status=status.HTTP_200_OK)

    def _process_operation(self, user, op):
        op_id = op['id']

        # Idempotence : déjà reçu, on ne rejoue rien.
        if JournalOperation.objects.filter(id=op_id).exists():
            return {'id': str(op_id), 'status': 'already_processed'}

        # Isolation : l'utilisateur doit appartenir à la boutique visée.
        store_belongs = UserStore.objects.filter(user=user, store_id=op['store_id']).exists()
        if not store_belongs:
            return {'id': str(op_id), 'status': 'error', 'message': 'Boutique non autorisée.'}

        journal_entry = None
        try:
            with transaction.atomic():
                journal_entry = JournalOperation.objects.create(
                    id=op_id,
                    store_id=op['store_id'],
                    user=user,
                    device_id=op.get('device_id'),
                    operation_type=op['operation_type'],
                    entity_type=op['entity_type'],
                    entity_id=op['entity_id'],
                    payload=op['payload'],
                    client_created_at=op['client_created_at'],
                )
                self._apply(journal_entry)
                journal_entry.applied = True
                journal_entry.save(update_fields=['applied'])
            return {'id': str(op_id), 'status': 'applied'}

        except Exception as exc:
            if journal_entry:
                journal_entry.error_message = str(exc)
                journal_entry.save(update_fields=['error_message'])
            return {'id': str(op_id), 'status': 'error', 'message': str(exc)}

    def _apply(self, op: JournalOperation):
        """Dispatcher métier. Un seul cas géré pour l'instant :
        c'est la seule entité qui existe déjà côté serveur.
        Ajouter un "elif" ici à chaque nouvelle entité (produits,
        ventes...) dans les phases futures."""
        if op.operation_type == JournalOperation.OperationType.UPDATE_STORE:
            store = Store.objects.get(id=op.entity_id)
            if 'name' in op.payload:
                store.name = op.payload['name']
            if 'address' in op.payload:
                store.address = op.payload['address']
            store.save()
        else:
            raise ValueError(f"Type d'opération non géré : {op.operation_type}")


class SyncBootstrapView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        store_ids = UserStore.objects.filter(user=user).values_list('store_id', flat=True)
        stores = Store.objects.filter(id__in=store_ids)

        roles_by_store = dict(
            UserStore.objects.filter(user=user).values_list('store_id', 'role')
        )
        for store in stores:
            store.user_role = roles_by_store.get(store.id)

        return Response({
            'stores': StoreSerializer(stores, many=True).data,
            # 'products': [...],   # ajouté quand Product existera côté serveur
            # 'customers': [...],  # idem
        })
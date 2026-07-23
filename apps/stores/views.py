# ============================================================
# FILE: apps/stores/views.py
# ============================================================
#
# StoreListCreateView
# --------------------
# GET  /api/stores/   → liste des boutiques de l'utilisateur connecté
#                       (propriétaire OU gérant, via UserStore)
# POST /api/stores/   → crée une boutique. L'utilisateur connecté
#                       devient automatiquement "owner" (création
#                       du Store + de la ligne UserStore dans la
#                       même transaction, pour ne jamais avoir une
#                       boutique orpheline sans propriétaire lié).
# ------------------------------------------------------
from django.db import transaction
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from apps.stores.models import Store, UserStore
from apps.stores.serializers import StoreSerializer, CreateStoreSerializer


class StoreListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return CreateStoreSerializer if self.request.method == 'POST' else StoreSerializer

    def get_queryset(self):
        # On ne renvoie que les boutiques auxquelles l'utilisateur
        # est rattaché via UserStore (owner OU manager) — jamais
        # toutes les boutiques de la base (isolation stricte).
        user = self.request.user
        store_ids = UserStore.objects.filter(user=user).values_list('store_id', flat=True)
        stores = Store.objects.filter(id__in=store_ids)

        # On injecte le rôle de CET utilisateur sur chaque boutique,
        # pour que StoreSerializer.get_role() puisse le lire.
        roles_by_store = dict(
            UserStore.objects.filter(user=user).values_list('store_id', 'role')
        )
        for store in stores:
            store.user_role = roles_by_store.get(store.id)
        return stores

    def create(self, request, *args, **kwargs):
        serializer = CreateStoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            store = serializer.save(owner=request.user)
            UserStore.objects.create(
                user=request.user,
                store=store,
                role=UserStore.Role.OWNER,
                status=UserStore.Status.ACTIVE,
            )

        store.user_role = UserStore.Role.OWNER
        return Response(StoreSerializer(store).data, status=status.HTTP_201_CREATED)
# ============================================================
# FILE: apps/stores/permissions.py
# ============================================================
#
# IsStoreOwner
# ------------
# Autorise uniquement le PROPRIÉTAIRE de la boutique visée
# (UserStore.role == owner) — utilisé pour tout ce qui touche aux
# gérants : inviter, révoquer une invitation, retirer un membre.
# Un gérant ne doit pas pouvoir gérer d'autres gérants (cohérent
# avec vision_produit.md : le gérant "ne peut pas gérer les
# abonnements ni modifier les paramètres globaux").
#
# Suppose que la vue a `kwargs['store_id']` (routes imbriquées
# sous /stores/<store_id>/...).
# ------------------------------------------------------
from rest_framework.permissions import BasePermission
from apps.stores.models import UserStore


class IsStoreOwner(BasePermission):
    message = "Seul le propriétaire de la boutique peut effectuer cette action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True  # laisse IsAuthenticated renvoyer le 401 approprié

        store_id = view.kwargs.get('store_id')
        return UserStore.objects.filter(
            user=request.user,
            store_id=store_id,
            role=UserStore.Role.OWNER,
        ).exists()
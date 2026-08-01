# apps/subscriptions/permissions.py
# ============================================================
# FILE: apps/subscriptions/permissions.py
# ============================================================
#
# HasWriteAccess
# ---------------
# Bloque les méthodes d'écriture (POST/PUT/PATCH/DELETE) si le
# crédit d'essai ou l'abonnement de l'utilisateur est expiré.
# Les lectures (GET/HEAD/OPTIONS) passent toujours — c'est la
# règle demandée : "lecture seule" en cas d'expiration, pas un
# blocage total.
#
# Ne gère pas l'authentification elle-même (has_permission renvoie
# True si l'utilisateur n'est pas authentifié) : c'est le rôle de
# IsAuthenticated, toujours combiné avec cette permission.
# ------------------------------------------------------
from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.subscriptions.services import get_subscription_status


class HasWriteAccess(BasePermission):
    message = (
        "Votre période d'essai ou votre abonnement a expiré. "
        "Passez à un plan payant pour continuer à modifier vos données."
    )

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return True  # laisse IsAuthenticated renvoyer le 401 approprié

        subscription_status = get_subscription_status(request.user)
        return not subscription_status.is_read_only
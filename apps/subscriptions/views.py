# apps/subscriptions/views.py
# ============================================================
# FILE: apps/subscriptions/views.py
# ============================================================
#
# PlanListView
# ------------
# GET /api/subscriptions/plans/ → liste des plans actifs, pour
# la page de choix d'abonnement.
#
# SubscribeView
# -------------
# POST /api/subscriptions/subscribe/ → souscrit l'utilisateur à un
# plan (simulé, pas de paiement réel). Volontairement SANS
# HasWriteAccess : un utilisateur en lecture seule doit pouvoir
# souscrire pour sortir de ce statut.
#
# MyStatusView
# ------------
# GET /api/subscriptions/my-status/ → statut courant, pour que
# Flutter sache s'il doit afficher un bandeau "lecture seule" et
# quand proposer un renouvellement.
# ------------------------------------------------------
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.subscriptions.models import SubscriptionPlan
from apps.subscriptions.serializers import (
    SubscriptionPlanSerializer,
    SubscriptionStatusSerializer,
)
from apps.subscriptions.services import get_subscription_status, subscribe_to_plan


class PlanListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionPlanSerializer
    queryset = SubscriptionPlan.objects.filter(is_active=True)


class SubscribeView(APIView):
    # Pas de HasWriteAccess ici : voir explication en Phase 3.
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'detail': 'Plan introuvable ou inactif.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        subscribe_to_plan(request.user, plan)
        new_status = get_subscription_status(request.user)
        return Response(
            SubscriptionStatusSerializer(new_status).data,
            status=status.HTTP_201_CREATED,
        )


class MyStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        current_status = get_subscription_status(request.user)
        return Response(SubscriptionStatusSerializer(current_status).data)
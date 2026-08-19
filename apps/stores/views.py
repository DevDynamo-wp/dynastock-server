# ============================================================
# FILE: apps/stores/views.py
# ============================================================
#
# StoreListCreateView            — inchangé (cf. commentaires d'origine)
# StoreInvitationListCreateView  — GET/POST /api/stores/<store_id>/invitations/  (owner uniquement)
# StoreInvitationRevokeView      — DELETE   /api/stores/<store_id>/invitations/<invitation_id>/
# AcceptInvitationView           — POST     /api/stores/invitations/accept/  (le gérant saisit son code)
# StoreMemberListView            — GET      /api/stores/<store_id>/members/
# StoreMemberRemoveView          — DELETE   /api/stores/<store_id>/members/<member_id>/
#                                   (jamais le owner lui-même, cf. get_queryset)
# ------------------------------------------------------
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.stores.emails import send_invitation_email
from apps.stores.models import Store, StoreInvitation, UserStore
from apps.stores.permissions import IsStoreOwner
from apps.stores.serializers import (
    AcceptInvitationSerializer,
    CreateInvitationSerializer,
    CreateStoreSerializer,
    MyInvitationSerializer,
    StoreInvitationSerializer,
    StoreMemberSerializer,
    StoreSerializer,
)
from apps.subscriptions.permissions import HasWriteAccess


class StoreListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, HasWriteAccess]

    def get_serializer_class(self):
        return CreateStoreSerializer if self.request.method == 'POST' else StoreSerializer

    def get_queryset(self):
        user = self.request.user
        store_ids = UserStore.objects.filter(user=user).values_list('store_id', flat=True)
        stores = Store.objects.filter(id__in=store_ids)

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


class StoreInvitationListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStoreOwner, HasWriteAccess]
    serializer_class = StoreInvitationSerializer

    def get_queryset(self):
        return StoreInvitation.objects.filter(
            store_id=self.kwargs['store_id'],
            status=StoreInvitation.Status.PENDING,
        ).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        input_serializer = CreateInvitationSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        email = input_serializer.validated_data['email']

        store = Store.objects.get(id=self.kwargs['store_id'])

        # On évite les doublons : déjà membre, ou déjà une invitation
        # en attente pour ce même email sur cette boutique.
        if UserStore.objects.filter(store=store, user__email__iexact=email).exists():
            raise ValidationError({'email': "Cette personne fait déjà partie de la boutique."})

        if StoreInvitation.objects.filter(
            store=store, invited_email__iexact=email, status=StoreInvitation.Status.PENDING,
        ).exists():
            raise ValidationError({'email': "Une invitation est déjà en attente pour cet email."})

        invitation = StoreInvitation.objects.create(
            store=store,
            invited_email=email,
            invited_by=request.user,
        )
        send_invitation_email(invitation)

        return Response(StoreInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)


class StoreInvitationRevokeView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStoreOwner, HasWriteAccess]
    lookup_url_kwarg = 'invitation_id'

    def get_queryset(self):
        return StoreInvitation.objects.filter(
            store_id=self.kwargs['store_id'],
            status=StoreInvitation.Status.PENDING,
        )

    def perform_destroy(self, instance):
        # On garde une trace (statut) plutôt que de supprimer la ligne.
        instance.status = StoreInvitation.Status.REVOKED
        instance.save(update_fields=['status'])


class AcceptInvitationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code'].upper()

        try:
            invitation = StoreInvitation.objects.get(code=code, status=StoreInvitation.Status.PENDING)
        except StoreInvitation.DoesNotExist:
            raise ValidationError({'code': "Code invalide ou déjà utilisé."})

        if invitation.is_expired:
            raise ValidationError({'code': "Ce code a expiré. Demandez une nouvelle invitation."})

        if invitation.invited_email.lower() != request.user.email.lower():
            raise PermissionDenied("Ce code n'a pas été envoyé à votre adresse email.")

        with transaction.atomic():
            user_store, _ = UserStore.objects.get_or_create(
                user=request.user,
                store=invitation.store,
                defaults={'role': invitation.role, 'status': UserStore.Status.ACTIVE},
            )
            invitation.status = StoreInvitation.Status.ACCEPTED
            invitation.save(update_fields=['status'])

        store = invitation.store
        store.user_role = user_store.role
        return Response(StoreSerializer(store).data, status=status.HTTP_200_OK)
    
    
class MyInvitationListView(generics.ListAPIView):
    """GET /api/stores/invitations/mine/
    Liste les invitations en attente pour l'utilisateur connecté,
    retrouvées par son email (pas besoin de code pour les VOIR —
    le code ne sert que si on veut les accepter via AcceptInvitationView).
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MyInvitationSerializer

    def get_queryset(self):
        return StoreInvitation.objects.filter(
            invited_email__iexact=self.request.user.email,
            status=StoreInvitation.Status.PENDING,
        ).select_related('store', 'invited_by').order_by('-created_at')


class RejectInvitationView(APIView):
    """POST /api/stores/invitations/<invitation_id>/reject/
    L'invité refuse une invitation qui lui est destinée.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invitation_id):
        try:
            invitation = StoreInvitation.objects.get(
                id=invitation_id,
                status=StoreInvitation.Status.PENDING,
            )
        except StoreInvitation.DoesNotExist:
            raise ValidationError("Invitation introuvable ou déjà traitée.")

        if invitation.invited_email.lower() != request.user.email.lower():
            raise PermissionDenied("Cette invitation ne vous est pas destinée.")

        invitation.status = StoreInvitation.Status.REJECTED
        invitation.save(update_fields=['status'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class StoreMemberListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStoreOwner]
    serializer_class = StoreMemberSerializer

    def get_queryset(self):
        return UserStore.objects.filter(
            store_id=self.kwargs['store_id'],
        ).select_related('user').order_by('-role', 'joined_at')


class StoreMemberRemoveView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStoreOwner, HasWriteAccess]
    lookup_url_kwarg = 'member_id'

    def get_queryset(self):
        # On exclut le owner : impossible de le "retirer" via cet
        # endpoint (il faudrait un transfert de propriété, V2).
        return UserStore.objects.filter(
            store_id=self.kwargs['store_id'],
        ).exclude(role=UserStore.Role.OWNER)
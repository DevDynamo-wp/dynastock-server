# ============================================================
# FILE: apps/stores/urls.py
# ============================================================
from django.urls import path
from apps.stores.views import (
    AcceptInvitationView,
    MyInvitationListView,
    RejectInvitationView,
    StoreInvitationListCreateView,
    StoreInvitationRevokeView,
    StoreListCreateView,
    StoreMemberListView,
    StoreMemberRemoveView,
)

urlpatterns = [
    path('', StoreListCreateView.as_view(), name='store-list-create'),

    # Pas de store_id dans l'URL : le code identifie la boutique lui-même.
    path('invitations/accept/', AcceptInvitationView.as_view(), name='invitation-accept'),

    # Invitations reçues par l'utilisateur connecté (par email), avant
    # toute liaison à une boutique — écran "Invitations".
    path('invitations/mine/', MyInvitationListView.as_view(), name='invitation-mine'),
    path(
        'invitations/<uuid:invitation_id>/reject/',
        RejectInvitationView.as_view(),
        name='invitation-reject',
    ),

    path(
        '<uuid:store_id>/invitations/',
        StoreInvitationListCreateView.as_view(),
        name='store-invitation-list-create',
    ),
    path(
        '<uuid:store_id>/invitations/<uuid:invitation_id>/',
        StoreInvitationRevokeView.as_view(),
        name='store-invitation-revoke',
    ),
    path(
        '<uuid:store_id>/members/',
        StoreMemberListView.as_view(),
        name='store-member-list',
    ),
    path(
        '<uuid:store_id>/members/<uuid:member_id>/',
        StoreMemberRemoveView.as_view(),
        name='store-member-remove',
    ),
]
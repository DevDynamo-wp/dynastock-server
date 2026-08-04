# ============================================================
# FILE: apps/stores/urls.py
# ============================================================
from django.urls import path
from apps.stores.views import (
    AcceptInvitationView,
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
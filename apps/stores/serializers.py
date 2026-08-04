# ============================================================
# FILE: apps/stores/serializers.py
# ============================================================
#
# StoreSerializer / CreateStoreSerializer
# ----------------------------------------
# Inchangés — cf. commentaires d'origine.
#
# CreateInvitationSerializer / StoreInvitationSerializer
# --------------------------------------------------------
# Création d'une invitation (juste l'email) et sa représentation
# (incluant le code, renvoyé pour que le propriétaire puisse le
# consulter/le renvoyer manuellement si besoin).
#
# AcceptInvitationSerializer
# ----------------------------
# Le gérant invité ne fournit que le code reçu par email.
#
# StoreMemberSerializer
# -----------------------
# Représentation d'un membre (UserStore) pour l'écran "Gérants".
# ------------------------------------------------------
from rest_framework import serializers
from apps.stores.models import Store, UserStore, StoreInvitation


class StoreSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = ['id', 'name', 'city', 'address', 'owner', 'role', 'created_at']
        read_only_fields = ['id', 'owner', 'created_at']

    def get_role(self, obj: Store) -> str:
        return getattr(obj, 'user_role', None)


class CreateStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['id', 'name', 'city', 'address']
        read_only_fields = ['id']


class CreateInvitationSerializer(serializers.Serializer):
    """Écriture uniquement : le propriétaire saisit juste l'email
    du futur gérant. store/role/invited_by sont déduits côté vue."""
    email = serializers.EmailField()


class StoreInvitationSerializer(serializers.ModelSerializer):
    """Représentation renvoyée après création et dans la liste des
    invitations en attente d'une boutique."""

    class Meta:
        model = StoreInvitation
        fields = ['id', 'invited_email', 'role', 'code', 'status', 'created_at', 'expires_at']
        read_only_fields = fields


class AcceptInvitationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=8)


class StoreMemberSerializer(serializers.ModelSerializer):
    """Un membre d'une boutique (propriétaire ou gérant), pour
    l'écran 'Gérants' (Niveau 4 du plan)."""
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = UserStore
        fields = ['id', 'email', 'full_name', 'role', 'status', 'joined_at']
        read_only_fields = fields
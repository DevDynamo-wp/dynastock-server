# ============================================================
# FILE: apps/stores/serializers.py
# ============================================================
#
# StoreSerializer
# ---------------
# Représentation d'une boutique. Le champ "role" est ajouté
# dynamiquement (il ne vient pas du modèle Store lui-même mais
# de la relation UserStore) : utile côté Flutter pour savoir si
# l'utilisateur connecté est propriétaire ou gérant de cette
# boutique, sans requête supplémentaire.
#
# CreateStoreSerializer
# ----------------------
# Utilisé uniquement en écriture (création) : on ne demande que
# les champs saisis par l'utilisateur, "owner" est déduit du
# token JWT, jamais envoyé par le client (sécurité).
# ------------------------------------------------------
from rest_framework import serializers
from apps.stores.models import Store


class StoreSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = ['id', 'name', 'city', 'address', 'owner', 'role', 'created_at']
        read_only_fields = ['id', 'owner', 'created_at']

    def get_role(self, obj: Store) -> str:
        # "user_role" est injecté par la vue (voir StoreListView),
        # car il dépend de QUI regarde la boutique, pas de la
        # boutique elle-même.
        return getattr(obj, 'user_role', None)


class CreateStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['id', 'name', 'city', 'address']
        read_only_fields = ['id']
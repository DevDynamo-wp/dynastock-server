# ============================================================
# FILE: apps/stores/models.py
# ============================================================
#
# Store
# -----
# Une boutique appartient à un propriétaire (owner). Isolation
# stricte des données : tout ce qui est lié à une boutique (
# produits, ventes...) référencera store_id, jamais directement
# l'utilisateur — conforme à la vision produit.
#
# UserStore
# ---------
# Relation "enrichie" Utilisateur <-> Boutique (cf. relations.md :
# on ne fait pas un simple lien direct car cette relation porte
# une donnée propre : le rôle, et plus tard le statut d'invitation
# pour les gérants).
# ------------------------------------------------------
import uuid
from django.db import models
from apps.accounts.models import User


class Store(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True, null=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_stores')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UserStore(models.Model):
    """
    Table de liaison Utilisateur <-> Boutique.
    Le propriétaire ET les futurs gérants passeront par cette table.
    """

    class Role(models.TextChoices):
        OWNER = 'owner', 'Propriétaire'
        MANAGER = 'manager', 'Gérant'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Actif'
        INVITED = 'invited', 'Invité'  # utile plus tard pour les gérants

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_links')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='user_links')

    role = models.CharField(max_length=10, choices=Role.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Un même utilisateur ne peut pas être lié deux fois à la même boutique
        unique_together = ('user', 'store')

    def __str__(self):
        return f"{self.user.email} → {self.store.name} ({self.role})"
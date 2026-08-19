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
# une donnée propre : le rôle, et le statut d'invitation pour les
# gérants).
#
# StoreInvitation
# ----------------
# Invitation d'un gérant sur une boutique, par email + code à 8
# caractères. Le gérant reçoit le code par email et le saisit
# manuellement dans l'app (écran "Rejoindre une boutique") — pas
# de deep link, décision produit pour éviter la configuration
# native (App Links / Universal Links).
# ------------------------------------------------------
import secrets
import uuid
from datetime import timedelta

from django.conf import settings as django_settings
from django.db import models
from django.utils import timezone

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
    Le propriétaire ET les gérants passent par cette table.
    """

    class Role(models.TextChoices):
        OWNER = 'owner', 'Propriétaire'
        MANAGER = 'manager', 'Gérant'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Actif'
        INVITED = 'invited', 'Invité'  # conservé pour compat, non utilisé par le flux code

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


def _generate_invitation_code() -> str:
    """Code court et facile à recopier à la main : 8 caractères,
    alphabet volontairement restreint (pas de 0/O ni 1/I, trop
    faciles à confondre en le retapant depuis un email)."""
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(alphabet) for _ in range(8))


class StoreInvitation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        ACCEPTED = 'accepted', 'Acceptée'
        REVOKED = 'revoked', 'Révoquée'      # révoquée par le propriétaire
        REJECTED = 'rejected', 'Rejetée'     # rejetée par l'invité lui-même

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='invitations')
    invited_email = models.EmailField()

    # Seul 'manager' est invitable pour l'instant : le propriétaire
    # ne s'invite pas lui-même sur sa propre boutique.
    role = models.CharField(max_length=10, choices=UserStore.Role.choices, default=UserStore.Role.MANAGER)

    code = models.CharField(max_length=8, unique=True, default=_generate_invitation_code)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            days = getattr(django_settings, 'INVITATION_VALIDITY_DAYS', 7)
            self.expires_at = timezone.now() + timedelta(days=days)
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.invited_email} → {self.store.name} ({self.status})"
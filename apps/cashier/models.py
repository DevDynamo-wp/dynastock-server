# ============================================================
# FILE: apps/cashier/models.py
# ============================================================
#
# CashSession
# -----------
# Une session de caisse = une plage "ouverture -> fermeture"
# sur une boutique. Une seule session OPEN à la fois par
# boutique (contrainte appliquée côté application, pas en base —
# cf. la même logique que pour le flux offline-first : le
# contrôle vit dans le repository Flutter, le serveur enregistre
# ce qu'on lui envoie).
#
# `expected_amount` est calculé côté Flutter au moment de la
# fermeture (opening_amount + somme des ventes de la session) et
# envoyé tel quel — le serveur ne recalcule pas depuis les ventes
# pour rester cohérent avec le principe "journal d'opérations"
# (pas de recalcul serveur qui pourrait diverger de ce que
# l'utilisateur voit à l'écran au moment de compter sa caisse).
#
# `difference` = closing_amount - expected_amount. Positif = trop
# perçu, négatif = manque en caisse.
# ------------------------------------------------------
import uuid

from django.db import models

from apps.accounts.models import User
from apps.stores.models import Store


class CashSession(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Ouverte'
        CLOSED = 'closed', 'Fermée'

    id = models.UUIDField(primary_key=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='cash_sessions')

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    opened_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opened_cash_sessions')
    opening_amount = models.DecimalField(max_digits=12, decimal_places=2)
    opened_at = models.DateTimeField()

    closed_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='closed_cash_sessions',
        null=True, blank=True,
    )
    closing_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    difference = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.store.name} — {self.opened_at:%d/%m/%Y} ({self.status})'
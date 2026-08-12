# ============================================================
# FILE: apps/expenses/models.py
# ============================================================
#
# Expense
# -------
# Une dépense de boutique (loyer, électricité, transport,
# salaires, divers...). Même logique que Category/Supplier :
# l'id est généré côté Flutter (création possible hors ligne),
# le serveur se contente de l'enregistrer via le journal
# (cf. apps/sync/views.py).
#
# `category` est un CharField libre (pas un modèle séparé) :
# une dépense n'a pas besoin d'un catalogue de catégories géré à
# part comme les produits — un simple libellé suffit pour ce que
# demande le cahier des charges SalePro ("Gestion des dépenses").
# ------------------------------------------------------
import uuid

from django.db import models

from apps.stores.models import Store


class Expense(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='expenses')

    category = models.CharField(max_length=100, blank=True, default='')
    description = models.CharField(max_length=255, blank=True, default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    expense_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.category or "Dépense"} — {self.amount}'
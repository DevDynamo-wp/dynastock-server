# ============================================================
# FILE: apps/sync/models.py
# ============================================================
#
# JournalOperation
# -----------------
# Version serveur du journal d'opérations local (cf. vision_produit.md).
# Point clé : l'id N'EST PAS généré ici, il vient du téléphone.
# C'est ce qui permet la dé-duplication : si Flutter renvoie deux
# fois la même opération (ex: connexion coupée juste après la
# confirmation serveur), on reconnaît l'id déjà traité et on ne
# rejoue rien.
# ------------------------------------------------------
from django.db import models
from apps.accounts.models import User
from apps.stores.models import Store


class JournalOperation(models.Model):

    class OperationType(models.TextChoices):
        UPDATE_STORE = 'UPDATE_STORE', 'Modifier une boutique'
        CREATE_CATEGORY = 'CREATE_CATEGORY', 'Créer une catégorie'
        UPDATE_CATEGORY = 'UPDATE_CATEGORY', 'Modifier une catégorie'
        CREATE_PRODUCT = 'CREATE_PRODUCT', 'Créer un produit'
        UPDATE_PRODUCT = 'UPDATE_PRODUCT', 'Modifier un produit'
        CREATE_SUPPLIER = 'CREATE_SUPPLIER', 'Créer un fournisseur'
        UPDATE_SUPPLIER = 'UPDATE_SUPPLIER', 'Modifier un fournisseur'
        CREATE_CUSTOMER = 'CREATE_CUSTOMER', 'Créer un client'
        UPDATE_CUSTOMER = 'UPDATE_CUSTOMER', 'Modifier un client'
        CREATE_SALE = 'CREATE_SALE', 'Créer une vente'
        CREATE_RESTOCK = 'CREATE_RESTOCK', 'Réapprovisionner'
        CREATE_ADJUSTMENT = 'CREATE_ADJUSTMENT', 'Ajuster le stock'
        CREATE_INVENTORY_COUNT = 'CREATE_INVENTORY_COUNT', 'Comptage d\'inventaire'
        CREATE_EXPENSE = 'CREATE_EXPENSE', 'Créer une dépense'
        UPDATE_EXPENSE = 'UPDATE_EXPENSE', 'Modifier une dépense'
        DELETE_EXPENSE = 'DELETE_EXPENSE', 'Supprimer une dépense'
        CREATE_CASH_SESSION = 'CREATE_CASH_SESSION', 'Ouvrir une session de caisse'
        CLOSE_CASH_SESSION = 'CLOSE_CASH_SESSION', 'Fermer une session de caisse'
        CREATE_PURCHASE = 'CREATE_PURCHASE', 'Créer un achat'
        CREATE_EMPLOYEE = 'CREATE_EMPLOYEE', 'Créer un employé'
        UPDATE_EMPLOYEE = 'UPDATE_EMPLOYEE', 'Modifier un employé'
        DELETE_EMPLOYEE = 'DELETE_EMPLOYEE', 'Supprimer un employé'

    id = models.UUIDField(primary_key=True, editable=False)

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='journal_operations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_operations')

    # Pas encore utilisé côté Flutter aujourd'hui, mais prévu dès
    # maintenant : essentiel plus tard pour résoudre les conflits
    # entre plusieurs appareils (cf. relations.md).
    device_id = models.CharField(max_length=100, blank=True, null=True)

    operation_type = models.CharField(max_length=30, choices=OperationType.choices)
    entity_type = models.CharField(max_length=30)
    entity_id = models.CharField(max_length=64)
    payload = models.JSONField()

    applied = models.BooleanField(default=False)
    error_message = models.CharField(max_length=255, blank=True, null=True)

    client_created_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['client_created_at']

    def __str__(self):
        return f"{self.operation_type} on {self.entity_type}:{self.entity_id}"
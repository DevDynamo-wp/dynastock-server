# ============================================================
# FILE: catalog/models.py
# ============================================================
#
# Category
# --------
# L'id N'EST PAS attribué par le serveur (contrairement à Store) :
# il est généré côté Flutter au moment de la création, car une
# catégorie peut être créée hors ligne. Le serveur se contente de
# recevoir cet id via le journal et de créer la ligne avec.
# ------------------------------------------------------
import uuid
from django.db import models
from apps.stores.models import Store


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    """
    Produit vendable, rattaché à une boutique et (optionnellement)
    à une catégorie.

    Comme Category, l'id N'EST PAS attribué par le serveur : il est
    généré côté Flutter au moment de la création, car un produit
    peut être créé hors ligne (cf. vision_produit.md).

    Note de conception : `quantity` est initialisé ici à la
    création, mais ne sera PLUS modifié directement par la suite.
    Une fois la phase "Inventory" implémentée, les changements de
    stock passeront exclusivement par des mouvements journalisés
    (SALE, RESTOCK...) rejoués sur le serveur — jamais par un
    UPDATE_PRODUCT qui écraserait la quantité. On reste fidèle au
    principe du journal d'opérations plutôt que du "remplacement".
    """
    id = models.UUIDField(primary_key=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )

    name = models.CharField(max_length=150)
    reference = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, null=True)

    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)

    quantity = models.IntegerField(default=0)
    minimum_quantity = models.IntegerField(default=0)
    unit = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
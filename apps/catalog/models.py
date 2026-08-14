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

    expiry_date = models.DateField(
        null=True, blank=True,
        help_text="Date de péremption (facultative — secteurs concernés uniquement)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    
class Supplier(models.Model):
    """
    Fournisseur (Module 9). Même logique que Category/Product :
    l'id est généré côté Flutter (création possible hors ligne),
    le serveur se contente de l'enregistrer via le journal.

    Volontairement simple pour la V1 : pas de suivi d'achats ni
    de solde — juste un répertoire de contacts, prêt à être relié
    au futur module "Achats" (V2 de la roadmap).
    """
    id = models.UUIDField(primary_key=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='suppliers')

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True, default='')
    address = models.CharField(max_length=255, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    
class Customer(models.Model):
    """
    Client (Module 8). Même logique que Supplier : l'id est généré
    côté Flutter (création hors ligne possible), le serveur enregistre
    via le journal.

    debtAmount : dette client accumulée (payements différés).
    Initialisé à 0, modifié uniquement par des mouvements financiers
    (Vente crédit, Paiement) dans les phases futures (V3+).
    Pour l'instant, c'est un tracker simple pour la gestion manuelle.
    """
    id = models.UUIDField(primary_key=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='customers')

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True, default='')
    address = models.CharField(max_length=255, blank=True, default='')
    remark = models.TextField(blank=True, default='')

    debt_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Dette client accumulée'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    
class Sale(models.Model):
    """
    Vente (Module 6 - Inventory). Une transaction avec un client 
    (optionnel, vente anonyme possible) et des lignes de produits.
    
    L'id est généré côté Flutter. Le serveur le reçoit via le journal
    et enregistre la vente.
    
    Chaque vente génère automatiquement des mouvements de stock
    (sorties) lors de la création côté serveur, via _create_stock_movements().
    """
    id = models.UUIDField(primary_key=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='sales')
    customer = models.ForeignKey(
        'Customer', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sales'
    )
    user = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sales'
    )

    # Totaux calculés : actualisés lors de la création/modif des lignes
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_quantity = models.IntegerField(default=0)

    # Métadonnées
    sale_date = models.DateTimeField()  # Moment de la vente (côté client)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp du serveur

    class Meta:
        ordering = ['-sale_date']

    def __str__(self):
        return f"Vente {self.id} ({self.total_quantity} items)"


class SaleLine(models.Model):
    """
    Ligne de vente : chaque produit vendu dans une vente.
    
    Stocke le prix AU MOMENT DE LA VENTE (pas une FK vers le prix
    courant du produit) : historique immuable des transactions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_lines')

    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)  # Prix à la vente
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)  # quantity * unit_price

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
    
    
class Purchase(models.Model):
    """
    Achat fournisseur (Module Achats). Miroir de Sale, mais côté
    entrée de stock plutôt que sortie : un fournisseur (optionnel,
    achat "libre" possible) et des lignes de produits.

    L'id est généré côté Flutter. Chaque ligne génère un mouvement
    de stock RESTOCK côté serveur, comme Sale le fait pour ses
    sorties (_create_stock_movements()).
    """
    id = models.UUIDField(primary_key=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='purchases')
    supplier = models.ForeignKey(
        'Supplier', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='purchases'
    )
    user = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='purchases'
    )

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_quantity = models.IntegerField(default=0)

    purchase_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Achat {self.id} — {self.store.name}'


class PurchaseLine(models.Model):
    """
    Ligne d'achat : chaque produit reçu dans cet achat. Stocke le
    coût AU MOMENT DE L'ACHAT (pas une FK vers purchase_price
    courant du produit) — même principe que SaleLine.unit_price :
    historique immuable, purchase_price du produit n'est PAS
    modifié automatiquement (choix produit assumé).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='purchase_lines')

    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)


class StockMovement(models.Model):
    """
    Mouvement de stock (Module 6 - Inventory). Enregistre chaque
    variation (vente, réappro, ajustement, comptage d'inventaire).

    note : texte libre (motif d'ajustement, "Comptage physique"...).
    customer : dénormalisé depuis Sale.customer au moment de la
    création, pour retrouver rapidement l'historique d'achats d'un
    client sans jointure supplémentaire (cf. CustomerDetailPage).
    """
    class MovementType(models.TextChoices):
        SALE = 'SALE', 'Vente'
        RESTOCK = 'RESTOCK', 'Réapprovisionnement'
        ADJUSTMENT = 'ADJUSTMENT', 'Ajustement'
        INVENTORY = 'INVENTORY', 'Comptage d\'inventaire'
        TRANSFER = 'TRANSFER', 'Transfert'  # V2+

    id = models.UUIDField(primary_key=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stock_movements')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='stock_movements')
    user = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_movements'
    )

    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity_delta = models.IntegerField()
    note = models.CharField(max_length=255, blank=True, null=True)

    sale = models.ForeignKey(
        Sale, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_movements'
    )
    customer = models.ForeignKey(
        'Customer', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_movements'
    )

    # Métadonnées
    movement_date = models.DateTimeField()  # Moment du mouvement (côté client)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-movement_date']

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.product.name} ({self.quantity_delta:+d})"
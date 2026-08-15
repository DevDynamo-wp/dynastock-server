# ============================================================
# FILE: sync/views.py
# ============================================================
#
# SyncPushView
# ------------
# POST /api/sync/push/  → reçoit un lot d'opérations et les
# applique une par une, de façon idempotente.
#
# SyncBootstrapView
# ------------------
# GET /api/sync/bootstrap/  → renvoie tout ce dont Flutter a besoin
# pour reconstruire sa base locale après une réinstallation.
# Pour l'instant : uniquement les boutiques. La clé "stores" restera
# stable ; on ajoutera de nouvelles clés (products, customers...)
# au fil des prochaines phases, sans jamais casser ce qui existe.
# ------------------------------------------------------
import uuid

from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.stores.models import Store, UserStore
from apps.stores.serializers import StoreSerializer
from apps.sync.models import JournalOperation
from apps.sync.serializers import PushSerializer
from apps.catalog.models import Category, Product, Supplier, Customer, Sale, SaleLine, Purchase, PurchaseLine, StockMovement
from apps.catalog.serializers import (
    CategorySerializer, ProductSerializer, SupplierSerializer, 
    CustomerSerializer, SaleSerializer, PurchaseSerializer, StockMovementSerializer
)
from apps.cashier.models import CashSession
from apps.cashier.serializers import CashSessionSerializer
from apps.expenses.models import Expense
from apps.expenses.serializers import ExpenseSerializer

from apps.subscriptions.permissions import HasWriteAccess
from django.db.models import F

class SyncPushView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasWriteAccess]

    def post(self, request):
        serializer = PushSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        results = [
            self._process_operation(request.user, op)
            for op in serializer.validated_data['operations']
        ]
        return Response({'results': results}, status=status.HTTP_200_OK)

    def _process_operation(self, user, op):
        op_id = op['id']

        # Idempotence : déjà reçu, on ne rejoue rien.
        if JournalOperation.objects.filter(id=op_id).exists():
            return {'id': str(op_id), 'status': 'already_processed'}

        # Isolation : l'utilisateur doit appartenir à la boutique visée.
        store_belongs = UserStore.objects.filter(user=user, store_id=op['store_id']).exists()
        if not store_belongs:
            return {'id': str(op_id), 'status': 'error', 'message': 'Boutique non autorisée.'}

        journal_entry = None
        try:
            with transaction.atomic():
                journal_entry = JournalOperation.objects.create(
                    id=op_id,
                    store_id=op['store_id'],
                    user=user,
                    device_id=op.get('device_id'),
                    operation_type=op['operation_type'],
                    entity_type=op['entity_type'],
                    entity_id=op['entity_id'],
                    payload=op['payload'],
                    client_created_at=op['client_created_at'],
                )
                self._apply(journal_entry)
                journal_entry.applied = True
                journal_entry.save(update_fields=['applied'])
            return {'id': str(op_id), 'status': 'applied'}

        except Exception as exc:
            if journal_entry:
                journal_entry.error_message = str(exc)
                journal_entry.save(update_fields=['error_message'])
            return {'id': str(op_id), 'status': 'error', 'message': str(exc)}

    def _apply(self, op: JournalOperation):
        """Dispatcher métier. Un seul cas géré pour l'instant :
        c'est la seule entité qui existe déjà côté serveur.
        Ajouter un "elif" ici à chaque nouvelle entité (produits,
        ventes...) dans les phases futures."""
        if op.operation_type == JournalOperation.OperationType.UPDATE_STORE:
            store = Store.objects.get(id=op.entity_id)
            if 'name' in op.payload:
                store.name = op.payload['name']
            if 'address' in op.payload:
                store.address = op.payload['address']
            store.save()

        elif op.operation_type == JournalOperation.OperationType.CREATE_CATEGORY:
            Category.objects.create(
                id=op.entity_id,
                store_id=op.store_id,
                name=op.payload['name'],
            )

        elif op.operation_type == JournalOperation.OperationType.UPDATE_CATEGORY:
            category = Category.objects.get(id=op.entity_id)
            if 'name' in op.payload:
                category.name = op.payload['name']
            category.save()
            
        elif op.operation_type == JournalOperation.OperationType.CREATE_PRODUCT:
            Product.objects.create(
                id=op.entity_id,
                store_id=op.store_id,
                category_id=op.payload.get('category_id'),
                name=op.payload['name'],
                reference=op.payload['reference'],
                barcode=op.payload.get('barcode'),
                image_url=op.payload.get('image_url', ''),
                purchase_price=op.payload['purchase_price'],
                selling_price=op.payload['selling_price'],
                quantity=op.payload.get('quantity', 0),
                minimum_quantity=op.payload.get('minimum_quantity', 0),
                unit=op.payload['unit'],
                expiry_date=op.payload.get('expiry_date'),
            )

        elif op.operation_type == JournalOperation.OperationType.UPDATE_PRODUCT:
            # Ne touche jamais à `quantity` : voir la note dans catalog/models.py.
            product = Product.objects.get(id=op.entity_id)
            for field in ('category_id', 'name', 'reference', 'barcode',
                        'image_url', 'purchase_price', 'selling_price',
                        'minimum_quantity', 'unit', 'expiry_date'):
                payload_key = 'category_id' if field == 'category_id' else field
                if payload_key in op.payload:
                    setattr(product, field, op.payload[payload_key])
            product.save()
            
        elif op.operation_type == JournalOperation.OperationType.CREATE_SUPPLIER:
            Supplier.objects.create(
                id=op.entity_id,
                store_id=op.store_id,
                name=op.payload['name'],
                phone=op.payload.get('phone', ''),
                address=op.payload.get('address', ''),
            )

        elif op.operation_type == JournalOperation.OperationType.UPDATE_SUPPLIER:
            supplier = Supplier.objects.get(id=op.entity_id)
            for field in ('name', 'phone', 'address'):
                if field in op.payload:
                    setattr(supplier, field, op.payload[field])
            supplier.save()
            
        elif op.operation_type == JournalOperation.OperationType.CREATE_CUSTOMER:
            Customer.objects.create(
                id=op.entity_id,
                store_id=op.store_id,
                name=op.payload['name'],
                phone=op.payload.get('phone', ''),
                address=op.payload.get('address', ''),
                remark=op.payload.get('remark', ''),
                debt_amount=op.payload.get('debt_amount', 0),
            )

        elif op.operation_type == JournalOperation.OperationType.UPDATE_CUSTOMER:
            customer = Customer.objects.get(id=op.entity_id)
            for field in ('name', 'phone', 'address', 'remark', 'debt_amount'):
                if field in op.payload:
                    setattr(customer, field, op.payload[field])
            customer.save()
            
        elif op.operation_type == JournalOperation.OperationType.CREATE_SALE:
            self._create_sale(op)
            
        elif op.operation_type == JournalOperation.OperationType.CREATE_PURCHASE:
            self._create_purchase(op)

        elif op.operation_type == JournalOperation.OperationType.CREATE_RESTOCK:
            self._create_stock_movement(op, StockMovement.MovementType.RESTOCK)

        elif op.operation_type == JournalOperation.OperationType.CREATE_ADJUSTMENT:
            self._create_stock_movement(op, StockMovement.MovementType.ADJUSTMENT)
            
        elif op.operation_type == JournalOperation.OperationType.CREATE_INVENTORY_COUNT:
            self._create_stock_movement(op, StockMovement.MovementType.INVENTORY)
            
        elif op.operation_type == JournalOperation.OperationType.CREATE_EXPENSE:
            Expense.objects.create(
                id=op.entity_id,
                store_id=op.store_id,
                category=op.payload.get('category', ''),
                description=op.payload.get('description', ''),
                amount=op.payload['amount'],
                expense_date=op.payload['expense_date'],
            )

        elif op.operation_type == JournalOperation.OperationType.UPDATE_EXPENSE:
            expense = Expense.objects.get(id=op.entity_id)
            for field in ('category', 'description', 'amount', 'expense_date'):
                if field in op.payload:
                    setattr(expense, field, op.payload[field])
            expense.save()

        elif op.operation_type == JournalOperation.OperationType.DELETE_EXPENSE:
            Expense.objects.filter(id=op.entity_id).delete()
            
        elif op.operation_type == JournalOperation.OperationType.CREATE_CASH_SESSION:
            CashSession.objects.create(
                id=op.entity_id,
                store_id=op.store_id,
                opened_by_id=op.payload['opened_by'],
                opening_amount=op.payload['opening_amount'],
                opened_at=op.payload['opened_at'],
            )

        elif op.operation_type == JournalOperation.OperationType.CLOSE_CASH_SESSION:
            session = CashSession.objects.get(id=op.entity_id)
            session.status = CashSession.Status.CLOSED
            session.closed_by_id = op.payload['closed_by']
            session.closing_amount = op.payload['closing_amount']
            session.expected_amount = op.payload['expected_amount']
            session.difference = op.payload['difference']
            session.closed_at = op.payload['closed_at']
            session.save()

        else:
            raise ValueError(f"Type d'opération non géré : {op.operation_type}")
    
        
    def _create_sale(self, op: JournalOperation):
        """
        Crée une vente et ses lignes depuis le payload, puis génère
        automatiquement des mouvements de stock (sorties).
        
        Payload attendu :
        {
            'customer_id': null ou UUID,
            'sale_date': ISO8601,
            'lines': [
                {'product_id': UUID, 'quantity': int, 'unit_price': decimal},
                ...
            ]
        }
        """
        payload = op.payload
        customer_id = payload.get('customer_id')
        
        sale = Sale.objects.create(
            id=op.entity_id,
            store_id=op.store_id,
            customer_id=customer_id,
            user=op.user,
            sale_date=payload['sale_date'],
        )
        
        total_amount = 0
        total_quantity = 0
        
        for line_data in payload.get('lines', []):
            product_id = line_data['product_id']
            quantity = line_data['quantity']
            unit_price = line_data['unit_price']
            subtotal = quantity * unit_price
            
            SaleLine.objects.create(
                sale=sale,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            )
            
            total_amount += subtotal
            total_quantity += quantity
            
            # Génère un mouvement de stock (sortie = quantité négative)
            StockMovement.objects.create(
                id=str(uuid.uuid4()),
                store_id=op.store_id,
                product_id=product_id,
                user=op.user,
                movement_type=StockMovement.MovementType.SALE,
                quantity_delta=-quantity,  # Négatif = sortie
                sale=sale,
                customer_id=customer_id,
                movement_date=payload['sale_date'],
            )

            # ⭐ LA LIGNE QUI MANQUAIT : applique enfin le mouvement au
            # stock réel. F('quantity') = update atomique côté SQL,
            # évite un race condition si deux ventes du même produit
            # arrivent en même temps sur deux appareils différents.
            Product.objects.filter(id=product_id).update(
                quantity=F('quantity') - quantity
            )
        
        sale.total_amount = total_amount
        sale.total_quantity = total_quantity
        sale.save()
        
        
    def _create_purchase(self, op: JournalOperation):
        """
        Crée un achat et ses lignes depuis le payload, puis génère
        automatiquement des mouvements de stock (entrées).

        Payload attendu :
        {
            'supplier_id': null ou UUID,
            'purchase_date': ISO8601,
            'lines': [
                {'product_id': UUID, 'quantity': int, 'unit_cost': decimal},
                ...
            ]
        }
        """
        payload = op.payload
        supplier_id = payload.get('supplier_id')

        purchase = Purchase.objects.create(
            id=op.entity_id,
            store_id=op.store_id,
            supplier_id=supplier_id,
            user=op.user,
            purchase_date=payload['purchase_date'],
        )

        total_amount = 0
        total_quantity = 0

        for line_data in payload.get('lines', []):
            product_id = line_data['product_id']
            quantity = line_data['quantity']
            unit_cost = line_data['unit_cost']
            subtotal = quantity * unit_cost

            PurchaseLine.objects.create(
                purchase=purchase,
                product_id=product_id,
                quantity=quantity,
                unit_cost=unit_cost,
                subtotal=subtotal,
            )

            total_amount += subtotal
            total_quantity += quantity

            # Génère un mouvement de stock (entrée = quantité positive)
            StockMovement.objects.create(
                id=str(uuid.uuid4()),
                store_id=op.store_id,
                product_id=product_id,
                user=op.user,
                movement_type=StockMovement.MovementType.RESTOCK,
                quantity_delta=quantity,  # Positif = entrée
                purchase=purchase,
                movement_date=payload['purchase_date'],
            )

            # Même principe que _create_sale : update atomique F().
            Product.objects.filter(id=product_id).update(
                quantity=F('quantity') + quantity
            )

        purchase.total_amount = total_amount
        purchase.total_quantity = total_quantity
        purchase.save()
        

    def _create_stock_movement(self, op: JournalOperation, movement_type: str):
        """
        Crée un mouvement de stock (réappro, ajustement, inventaire)
        ET applique le delta au stock réel du produit.

        Un réapprovisionnement (RESTOCK) peut porter en plus :
        - supplier_id : fournisseur associé (optionnel)
        - new_purchase_price / new_selling_price : si les prix ont
          changé à ce réappro précis, on les enregistre ET on met à
          jour le produit (comme un UPDATE_PRODUCT), dans la même
          opération pour rester atomique.
        """
        payload = op.payload

        StockMovement.objects.create(
            id=op.entity_id,
            store_id=op.store_id,
            product_id=payload['product_id'],
            user=op.user,
            movement_type=movement_type,
            quantity_delta=payload['quantity_delta'],
            note=payload.get('reason') or payload.get('note'),
            supplier_id=payload.get('supplier_id'),
            new_purchase_price=payload.get('new_purchase_price'),
            new_selling_price=payload.get('new_selling_price'),
            movement_date=payload['movement_date'],
        )

        # ⭐ Idem : applique le delta au stock réel.
        Product.objects.filter(id=payload['product_id']).update(
            quantity=F('quantity') + payload['quantity_delta']
        )

        # Prix changés à ce réappro -> répercutés sur la fiche produit.
        price_updates = {}
        if payload.get('new_purchase_price') is not None:
            price_updates['purchase_price'] = payload['new_purchase_price']
        if payload.get('new_selling_price') is not None:
            price_updates['selling_price'] = payload['new_selling_price']
        if price_updates:
            Product.objects.filter(id=payload['product_id']).update(**price_updates)


class SyncBootstrapView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        store_ids = UserStore.objects.filter(user=user).values_list('store_id', flat=True)
        stores = Store.objects.filter(id__in=store_ids)
        categories = Category.objects.filter(store_id__in=store_ids)
        products = Product.objects.filter(store_id__in=store_ids)
        suppliers = Supplier.objects.filter(store_id__in=store_ids)
        customers = Customer.objects.filter(store_id__in=store_ids)
        expenses = Expense.objects.filter(store_id__in=store_ids)
        cash_sessions = CashSession.objects.filter(store_id__in=store_ids)
        purchases = Purchase.objects.filter(store_id__in=store_ids)
        sales = Sale.objects.filter(store_id__in=store_ids)
        stock_movements = StockMovement.objects.filter(store_id__in=store_ids)

        roles_by_store = dict(
            UserStore.objects.filter(user=user).values_list('store_id', 'role')
        )
        for store in stores:
            store.user_role = roles_by_store.get(store.id)

        return Response({
            'stores': StoreSerializer(stores, many=True).data,
            'categories': CategorySerializer(categories, many=True).data,
            'products': ProductSerializer(products, many=True).data,
            'suppliers': SupplierSerializer(suppliers, many=True).data,
            'customers': CustomerSerializer(customers, many=True).data,
            'expenses': ExpenseSerializer(expenses, many=True).data,
            'cash_sessions': CashSessionSerializer(cash_sessions, many=True).data,
            'purchases': PurchaseSerializer(purchases, many=True).data,
            'sales': SaleSerializer(sales, many=True).data,
            'stock_movements': StockMovementSerializer(stock_movements, many=True).data,
            # 'products': [...],   # ajouté quand Product existera côté serveur
            # 'customers': [...],  # idem
        })
# ============================================================
# FILE: catalog/serializers.py
# ============================================================
from rest_framework import serializers
from apps.catalog.models import Category, Product, Purchase, PurchaseLine, Supplier, Customer, Sale, SaleLine, StockMovement,Payment


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'store', 'name', 'created_at']
        


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'store', 'category', 'name', 'reference', 'barcode',
            'image_url', 'purchase_price', 'selling_price',
            'quantity', 'minimum_quantity', 'unit', 'expiry_date', 'created_at',
        ]
        
        
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'store', 'name', 'phone', 'address', 'debt_amount', 'created_at']        


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'store', 'name', 'phone', 'address', 'remark', 'debt_amount', 'created_at']
        
        
class SaleLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SaleLine
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'subtotal', 'created_at']


class SaleSerializer(serializers.ModelSerializer):
    lines = SaleLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Sale
        fields = ['id', 'store', 'customer', 'customer_name', 'user', 'total_amount', 'paid_amount',
                  'total_quantity', 'sale_date', 'lines', 'created_at']
        
        
class PurchaseLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PurchaseLine
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_cost', 'subtotal', 'created_at']


class PurchaseSerializer(serializers.ModelSerializer):
    lines = PurchaseLineSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)

    class Meta:
        model = Purchase
        fields = ['id', 'store', 'supplier', 'supplier_name', 'user', 'total_amount', 'paid_amount',
                  'total_quantity', 'purchase_date', 'lines', 'created_at']


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True, allow_null=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)

    class Meta:
        model = StockMovement
        fields = ['id', 'store', 'product', 'product_name', 'user', 'user_name', 'movement_type',
                  'quantity_delta', 'note', 'sale', 'customer', 'purchase', 'supplier',
                  'supplier_name', 'new_purchase_price', 'new_selling_price',
                  'movement_date', 'created_at']
        
        
        
class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True, allow_null=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)

    class Meta:
        model = Payment
        fields = ['id', 'store', 'direction', 'customer', 'customer_name', 'supplier', 'supplier_name',
                  'sale', 'purchase', 'amount', 'method', 'note', 'payment_date', 'created_at']
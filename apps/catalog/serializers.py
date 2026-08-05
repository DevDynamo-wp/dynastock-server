# ============================================================
# FILE: catalog/serializers.py
# ============================================================
from rest_framework import serializers
from apps.catalog.models import Category, Product, Supplier, Customer


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
            'quantity', 'minimum_quantity', 'unit', 'created_at',
        ]
        
        
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'store', 'name', 'phone', 'address', 'created_at']
        


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'store', 'name', 'phone', 'address', 'remark', 'debt_amount', 'created_at']
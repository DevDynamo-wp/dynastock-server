# ============================================================
# FILE: catalog/serializers.py
# ============================================================
from rest_framework import serializers
from apps.catalog.models import Category, Product


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
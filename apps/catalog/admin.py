# ============================================================
# FILE: apps/catalog/admin.py
# ============================================================
from django.contrib import admin
from apps.catalog.models import Category, Product, Supplier, Customer

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Supplier)
admin.site.register(Customer)
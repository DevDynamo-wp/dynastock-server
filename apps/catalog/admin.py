# ============================================================
# FILE: catalog/admin.py
# ============================================================
from django.contrib import admin
from apps.catalog.models import Category

admin.site.register(Category)
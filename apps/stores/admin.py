# ============================================================
# FILE: stores/admin.py
# ============================================================
from django.contrib import admin
from apps.stores.models import Store, UserStore

admin.site.register(Store)
admin.site.register(UserStore)
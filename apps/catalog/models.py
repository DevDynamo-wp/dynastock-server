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
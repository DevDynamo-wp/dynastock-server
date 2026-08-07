# ============================================================
# FILE: sync/admin.py
# ============================================================
from django.contrib import admin
from apps.sync.models import JournalOperation


@admin.register(JournalOperation)
class JournalOperationAdmin(admin.ModelAdmin):
    """
    Table de diagnostic : chaque opération journalisée reçue du
    téléphone, avec son statut d'application et le message d'erreur
    éventuel. C'est ICI qu'il faut regarder en premier quand une
    donnée créée dans Flutter n'apparaît pas côté serveur.
    """
    list_display = (
        'operation_type', 'entity_type', 'entity_id', 'store',
        'user', 'applied', 'error_message', 'client_created_at',
    )
    list_filter = ('operation_type', 'entity_type', 'applied')
    search_fields = ('entity_id', 'error_message')
    readonly_fields = [f.name for f in JournalOperation._meta.fields]
    ordering = ('-received_at',)
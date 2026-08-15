# ============================================================
# FILE: apps/employees/models.py
# ============================================================
#
# Employee
# --------
# Fiche RH d'une personne qui travaille dans la boutique (vendeur,
# caissier...). Distinct de UserStore (apps.stores) : UserStore
# représente un COMPTE APP (login, rôle owner/manager) ; Employee
# représente une PERSONNE (peut ne jamais se connecter à l'app —
# ex: un vendeur dont seul le propriétaire fait les ventes).
#
# `linked_member` est le pont optionnel entre les deux : si cet
# employé a AUSSI un compte gérant, on peut le relier ici. Reste
# nullable — beaucoup de petites boutiques n'auront jamais besoin
# de ce lien.
# ------------------------------------------------------
import uuid

from django.db import models

from apps.stores.models import Store, UserStore


class Employee(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='employees')

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True, default='')
    position = models.CharField(max_length=100, blank=True, default='')  # poste, texte libre

    hire_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    linked_member = models.ForeignKey(
        UserStore, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='employee_profile',
        help_text="Compte gérant lié (optionnel) — si cette personne a aussi accès à l'app."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} ({self.position or "Employé"}) — {self.store.name}'
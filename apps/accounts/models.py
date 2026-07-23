# ============================================================
# FILE: apps/accounts/models.py
# ============================================================
#
# User
# ----
# Modèle utilisateur personnalisé. Identifiant de connexion :
# l'email (pas de username). Le champ is_verified est prévu
# dès maintenant pour brancher l'OTP plus tard sans migration
# douloureuse (cf. explication donnée avant cette phase).
# ------------------------------------------------------
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from apps.accounts.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True, null=True)

    # Prévu pour l'OTP futur : True automatiquement pour l'instant
    is_verified = models.BooleanField(default=False)

    # Champs requis par Django pour l'admin et les permissions
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'       # champ utilisé pour se connecter
    REQUIRED_FIELDS = ['full_name']  # demandé par createsuperuser uniquement

    def __str__(self):
        return self.email
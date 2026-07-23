# ============================================================
# FILE: apps/accounts/managers.py
# ============================================================
#
# UserManager
# -----------
# Manager personnalisé car on utilise l'email comme identifiant
# de connexion (pas de "username" à la Django par défaut).
# Django ne fournit pas ce manager automatiquement dès qu'on
# personnalise AbstractBaseUser — il faut l'écrire soi-même.
# ------------------------------------------------------
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):

    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hash automatique, jamais en clair
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields):
        # Nécessaire pour pouvoir créer un compte admin via
        # "python manage.py createsuperuser"
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)
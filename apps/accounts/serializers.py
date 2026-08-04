# ============================================================
# FILE: apps/accounts/serializers.py
# ============================================================
#
# RegisterSerializer
# -------------------
# Valide les données d'inscription et crée l'utilisateur.
# is_verified est forcé à True ici car l'OTP n'est pas encore
# implémenté (cf. Phase 1). Quand l'OTP arrivera, il suffira
# de retirer cette ligne : le modèle a déjà is_verified=False
# par défaut, donc rien d'autre à casser.
#
# UserSerializer
# --------------
# Représentation "publique" de l'utilisateur, renvoyée dans les
# réponses d'API (jamais le mot de passe, bien sûr).
# ------------------------------------------------------
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone', 'is_verified', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone', 'password']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cet email.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            phone=validated_data.get('phone'),
        )
        # Temporaire : pas d'OTP pour l'instant, on active direct.
        # TODO(OTP) : retirer ces 2 lignes quand la vérif OTP arrivera.
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        return user
    
class UpdateProfileSerializer(serializers.ModelSerializer):
    """Sérialiseur utilisé uniquement pour PATCH /api/auth/me/.

    Volontairement restreint à full_name et phone : l'email est
    l'identifiant de connexion (USERNAME_FIELD) et ne doit pas être
    modifiable ici, pour ne pas risquer de casser les tokens/sessions
    existants ou créer des doublons non contrôlés.
    """

    class Meta:
        model = User
        fields = ['full_name', 'phone']
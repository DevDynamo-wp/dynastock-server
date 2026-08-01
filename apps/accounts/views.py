# ============================================================
# FILE: apps/accounts/views.py
# ============================================================
#
# RegisterView
# ------------
# POST /api/auth/register/  → crée le compte, renvoie tokens + profil.
# Renvoie directement les tokens (pas d'OTP pour l'instant) afin que
# Flutter puisse enchaîner immédiatement sur la création de boutique.
#
# LoginView
# ---------
# Surcharge de TokenObtainPairView pour renvoyer aussi le profil
# utilisateur en plus des tokens, en une seule requête.
#
# MeView
# ------
# GET /api/auth/me/  → profil de l'utilisateur connecté.
# Utile côté Flutter après une réinstallation : dès qu'on a un
# token valide, on peut revérifier qui est l'utilisateur avant
# de lancer le rapatriement des données (Phase 5).
# ------------------------------------------------------
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.serializers import RegisterSerializer, UserSerializer
from apps.accounts.models import User
from apps.subscriptions.services import start_trial


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        start_trial(user) # démarre le crédit gratuit configurable (TRIAL_CREDIT_DAYS)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class EmailTokenObtainSerializer(TokenObtainPairSerializer):
    """Identique au serializer standard : le login utilise déjà
    USERNAME_FIELD = 'email' défini sur le modèle User, donc pas
    de logique supplémentaire nécessaire ici — la classe existe
    pour rester explicite et pouvoir l'étendre plus tard (ex: bloquer
    la connexion si is_verified=False, une fois l'OTP en place)."""
    pass


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            email = request.data.get('email')
            user = User.objects.get(email__iexact=email)
            response.data['user'] = UserSerializer(user).data
        return response


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
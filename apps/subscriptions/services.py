# apps/subscriptions/services.py
# ============================================================
# FILE: apps/subscriptions/services.py
# ============================================================
#
# Toute la logique "l'utilisateur a-t-il le droit d'écrire ?" vit
# ici, séparée des vues et des modèles. Deux fonctions publiques :
#
#   - start_trial(user)        → appelée une seule fois, à l'inscription
#   - get_subscription_status(user) → appelée à chaque requête (par la
#                                      permission DRF de la Phase 3)
#
# get_subscription_status fait aussi de l'"expiration paresseuse" :
# plutôt qu'une tâche planifiée qui parcourt tous les users, on
# vérifie et on met à jour le statut au moment où on le consulte.
# Plus simple, et suffisant pour ce cas d'usage.
# ------------------------------------------------------
from dataclasses import dataclass
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from apps.subscriptions.models import Subscription


@dataclass
class SubscriptionStatus:
    """Résultat prêt à l'emploi pour l'API et pour la permission d'écriture."""

    status: str  # 'trial' | 'active' | 'expired' | 'none'
    is_read_only: bool
    end_date: "timezone.datetime | None"
    days_remaining: int


def start_trial(user) -> Subscription:
    """
    Crée le crédit gratuit initial. À appeler une seule fois,
    juste après la création du compte (RegisterView).
    """
    end_date = timezone.now() + timedelta(days=settings.TRIAL_CREDIT_DAYS)
    return Subscription.objects.create(
        user=user,
        plan=None,  # pas de plan payant pour l'essai gratuit
        status=Subscription.Status.TRIAL,
        end_date=end_date,
    )


def get_subscription_status(user) -> SubscriptionStatus:
    """
    Renvoie le statut d'accès courant de l'utilisateur.
    Si la période en cours (essai ou abonnement payant) est dépassée,
    elle est marquée EXPIRED en base au passage (expiration paresseuse).
    """
    current = Subscription.objects.filter(user=user).order_by("-start_date").first()

    if current is None:
        # Ne devrait pas arriver si start_trial() est bien appelé à
        # l'inscription, mais on protège quand même : accès en lecture
        # seule par défaut plutôt qu'une erreur serveur.
        return SubscriptionStatus(
            status="none", is_read_only=True, end_date=None, days_remaining=0
        )

    now = timezone.now()
    is_expired = current.end_date <= now
    active_statuses = {Subscription.Status.TRIAL, Subscription.Status.ACTIVE}

    if is_expired and current.status in active_statuses:
        current.status = Subscription.Status.EXPIRED
        current.save(update_fields=["status"])

    is_read_only = current.status not in active_statuses or is_expired
    days_remaining = max((current.end_date - now).days, 0) if not is_expired else 0

    return SubscriptionStatus(
        status=current.status,
        is_read_only=is_read_only,
        end_date=current.end_date,
        days_remaining=days_remaining,
    )
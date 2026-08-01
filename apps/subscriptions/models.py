# subscriptions/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone


class SubscriptionPlan(models.Model):
    """
    Une offre d'abonnement proposée au propriétaire de boutique
    (ex: Mensuel, Annuel). Le paiement est simulé pour le moment :
    aucune passerelle de paiement réelle n'est branchée.
    """

    class BillingPeriod(models.TextChoices):
        MONTHLY = "monthly", "Mensuel"
        YEARLY = "yearly", "Annuel"

    name = models.CharField(max_length=100)
    billing_period = models.CharField(max_length=10, choices=BillingPeriod.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(
        help_text="Nombre de jours d'accès offerts par ce plan."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Permet de retirer un plan de la vente sans le supprimer (garde l'historique intact).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["price"]

    def __str__(self):
        return f"{self.name} ({self.get_billing_period_display()})"


class Subscription(models.Model):
    """
    Historique des périodes d'accès d'un utilisateur : essai gratuit
    puis abonnements payants successifs. Un seul enregistrement est
    "actif" à un instant T pour un utilisateur donné.
    """

    class Status(models.TextChoices):
        TRIAL = "trial", "Essai gratuit"
        ACTIVE = "active", "Actif"
        EXPIRED = "expired", "Expiré"
        CANCELLED = "cancelled", "Annulé"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Vide pour l'essai gratuit initial (pas de plan payant associé).",
    )
    status = models.CharField(max_length=10, choices=Status.choices)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.user.email} — {self.get_status_display()} (jusqu'au {self.end_date:%Y-%m-%d})"
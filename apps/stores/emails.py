# ============================================================
# FILE: apps/stores/emails.py
# ============================================================
#
# send_invitation_email
# ------------------------
# Envoie le code d'invitation par email au gérant invité. Texte
# brut (pas de template HTML) : suffisant pour un code à recopier,
# et évite de maintenir un template en plus pour l'instant.
# ------------------------------------------------------
import logging
from django.conf import settings
from django.core.mail import send_mail
from apps.stores.models import StoreInvitation

logger = logging.getLogger(__name__)


def send_invitation_email(invitation: StoreInvitation) -> None:
    subject = f"Invitation à rejoindre {invitation.store.name} sur DynaStock"
    message = (
        f"Bonjour,\n\n"
        f"{invitation.invited_by.full_name} vous invite à rejoindre la boutique "
        f"\"{invitation.store.name}\" en tant que gérant sur DynaStock.\n\n"
        f"Pour accepter, ouvrez l'application DynaStock, allez dans "
        f"\"Rejoindre une boutique\" et saisissez ce code :\n\n"
        f"    {invitation.code}\n\n"
        f"Ce code est valable jusqu'au {invitation.expires_at.strftime('%d/%m/%Y')}.\n\n"
        f"Si vous n'attendiez pas cette invitation, ignorez simplement cet email."
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.invited_email],
            fail_silently=False,
        )
    except Exception:
        # L'invitation existe déjà en base avec son code : on ne fait
        # pas échouer toute la requête si seul l'envoi d'email rate.
        # Le propriétaire pourra toujours communiquer le code manuellement.
        logger.exception("Échec de l'envoi de l'email d'invitation à %s", invitation.invited_email)
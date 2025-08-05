# -*- coding: utf-8 -*-
import logging
from django.contrib.sessions.exceptions import SessionInterrupted
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse

logger = logging.getLogger(__name__)


class SessionErrorHandlerMiddleware:
    """
    Middleware pour gérer les erreurs de session de manière robuste
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Gère les exceptions de session
        """
        if isinstance(exception, SessionInterrupted):
            logger.warning(
                f"SessionInterrupted pour {request.path} - "
                f"User: {getattr(request.user, 'username', 'Anonymous')} - "
                f"Session key: {getattr(request.session, 'session_key', 'None')}"
            )

            # Nettoyer la session corrompue
            if hasattr(request, 'session'):
                try:
                    request.session.flush()
                except Exception as e:
                    logger.error(f"Erreur lors du nettoyage de session: {e}")

            # Redirection avec message d'information
            if request.path == '/signup/':
                messages.info(
                    request,
                    "Votre session a expiré. Veuillez réessayer votre inscription."
                )
                return HttpResponseRedirect(reverse('accounts:signup'))
            elif request.path == '/login/':
                messages.info(
                    request,
                    "Votre session a expiré. Veuillez réessayer votre connexion."
                )
                return HttpResponseRedirect(reverse('accounts:login'))
            else:
                messages.info(
                    request,
                    "Votre session a expiré. Vous avez été redirigé."
                )
                return HttpResponseRedirect(reverse('store:product_list'))

        # Retourner None pour laisser Django gérer les autres exceptions
        return None

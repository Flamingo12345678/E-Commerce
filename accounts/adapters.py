from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class CustomAccountAdapter(DefaultAccountAdapter):
    """Adaptateur personnalisé pour Django Allauth"""

    def get_login_redirect_url(self, request):
        """Redirection après connexion"""
        return "/"

    def get_logout_redirect_url(self, request):
        """Redirection après déconnexion"""
        return "/"

    def get_email_verification_redirect_url(self, email_address):
        """Redirection après confirmation d'email (nouvelle méthode)"""
        return reverse('accounts:profile')

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """Personnaliser l'envoi d'email de confirmation"""
        super().send_confirmation_mail(request, emailconfirmation, signup)
        if signup:
            messages.info(
                request,
                "Un email de confirmation a été envoyé à votre adresse. "
                "Veuillez cliquer sur le lien pour activer votre compte."
            )


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Adaptateur personnalisé pour l'authentification sociale"""

    def pre_social_login(self, request, sociallogin):
        """Actions avant la connexion sociale"""
        user = sociallogin.user
        if user.id:
            return

        # Vérifier si un utilisateur existe déjà avec cette adresse email
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            existing_user = User.objects.get(email=user.email)
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        """Sauvegarder l'utilisateur après connexion sociale"""
        user = super().save_user(request, sociallogin, form)

        # Récupérer les informations du profil social
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            if 'given_name' in extra_data and not user.first_name:
                user.first_name = extra_data['given_name']
            if 'family_name' in extra_data and not user.last_name:
                user.last_name = extra_data['family_name']

        elif sociallogin.account.provider == 'facebook':
            extra_data = sociallogin.account.extra_data
            if 'first_name' in extra_data and not user.first_name:
                user.first_name = extra_data['first_name']
            if 'last_name' in extra_data and not user.last_name:
                user.last_name = extra_data['last_name']

        user.save()
        return user

    def get_connect_redirect_url(self, request, socialaccount):
        """Redirection après connexion d'un compte social"""
        messages.success(request, f"Votre compte {socialaccount.provider.title()} a été connecté avec succès.")
        return reverse('accounts:profile')

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """Gestion des erreurs d'authentification sociale"""
        messages.error(
            request,
            f"Erreur lors de l'authentification avec {provider_id.title()}. Veuillez réessayer."
        )
        return redirect('account_login')

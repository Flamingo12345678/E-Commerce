from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import transaction
from allauth.account.views import SignupView, LoginView
from allauth.socialaccount.models import SocialAccount
from .forms import CustomSignupForm, CustomLoginForm, ProfileUpdateForm
from .models import Shopper
import json


class CustomSignupView(SignupView):
    """Vue d'inscription personnalisée utilisant Django Allauth"""
    form_class = CustomSignupForm
    template_name = 'account/signup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Créer un compte'
        return context


class CustomLoginView(LoginView):
    """Vue de connexion personnalisée utilisant Django Allauth"""
    form_class = CustomLoginForm
    template_name = 'account/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Se connecter'
        return context


@login_required
def profile(request):
    """Vue du profil utilisateur"""
    user = request.user

    # Récupérer les comptes sociaux liés
    social_accounts = SocialAccount.objects.filter(user=user)

    context = {
        'user': user,
        'social_accounts': social_accounts,
        'page_title': 'Mon profil',
        'has_google': social_accounts.filter(provider='google').exists(),
        'has_facebook': social_accounts.filter(provider='facebook').exists(),
    }

    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    """Vue d'édition du profil utilisateur"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {
        'form': form,
        'page_title': 'Modifier mon profil'
    }

    return render(request, 'accounts/profile_edit.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def change_password(request):
    """Vue de changement de mot de passe"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Vérifier le mot de passe actuel
        if not request.user.check_password(current_password):
            messages.error(request, 'Le mot de passe actuel est incorrect.')
            return render(request, 'accounts/change_password.html')

        # Vérifier que les nouveaux mots de passe correspondent
        if new_password != confirm_password:
            messages.error(request, 'Les nouveaux mots de passe ne correspondent pas.')
            return render(request, 'accounts/change_password.html')

        # Valider le nouveau mot de passe
        try:
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password, request.user)
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
            return render(request, 'accounts/change_password.html')

        # Changer le mot de passe
        request.user.set_password(new_password)
        request.user.save()

        messages.success(request, 'Votre mot de passe a été changé avec succès.')
        return redirect('accounts:profile')

    return render(request, 'accounts/change_password.html')


@login_required
def export_user_data(request):
    """Exporter les données utilisateur (RGPD)"""
    user = request.user

    # Préparer les données utilisateur
    user_data = {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_joined': user.date_joined.isoformat() if user.date_joined else None,
        'phone_number': user.phone_number if hasattr(user, 'phone_number') else None,
        'date_of_birth': user.date_of_birth.isoformat() if hasattr(user, 'date_of_birth') and user.date_of_birth else None,
        'marketing_emails_enabled': getattr(user, 'marketing_emails_enabled', False),
    }

    # Ajouter les comptes sociaux
    social_accounts = SocialAccount.objects.filter(user=user)
    user_data['social_accounts'] = []
    for account in social_accounts:
        user_data['social_accounts'].append({
            'provider': account.provider,
            'uid': account.uid,
            'date_joined': account.date_joined.isoformat(),
        })

    response = JsonResponse(user_data, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = 'attachment; filename="mes_donnees.json"'

    return response


@login_required
@require_http_methods(["POST"])
def delete_user_account(request):
    """Supprimer le compte utilisateur"""
    password = request.POST.get('password')

    if not request.user.check_password(password):
        messages.error(request, 'Mot de passe incorrect.')
        return redirect('accounts:profile')

    try:
        with transaction.atomic():
            # Supprimer l'utilisateur (les comptes sociaux seront supprimés automatiquement)
            request.user.delete()
            messages.success(request, 'Votre compte a été supprimé avec succès.')
            return redirect('/')
    except Exception as e:
        messages.error(request, 'Une erreur est survenue lors de la suppression de votre compte.')
        return redirect('accounts:profile')


@login_required
def manage_addresses(request):
    """Gérer les adresses de livraison"""
    # TODO: Implémenter la gestion des adresses
    context = {
        'page_title': 'Mes adresses'
    }
    return render(request, 'accounts/manage_addresses.html', context)


@login_required
def manage_payment_methods(request):
    """Gérer les méthodes de paiement"""
    # TODO: Implémenter la gestion des méthodes de paiement
    context = {
        'page_title': 'Mes méthodes de paiement'
    }
    return render(request, 'accounts/manage_payment_methods.html', context)


@login_required
@require_http_methods(["POST"])
def update_notifications(request):
    """Mettre à jour les préférences de notifications"""
    try:
        marketing_emails = request.POST.get('marketing_emails') == 'on'

        user = request.user
        user.marketing_emails_enabled = marketing_emails
        user.save()

        messages.success(request, 'Vos préférences de notifications ont été mises à jour.')
    except Exception as e:
        messages.error(request, 'Erreur lors de la mise à jour des préférences.')

    return redirect('accounts:profile')


@login_required
def setup_two_factor(request):
    """Configuration de l'authentification à deux facteurs"""
    from django_otp.plugins.otp_totp.models import TOTPDevice
    from django_otp import user_has_device

    user = request.user
    has_device = user_has_device(user)

    if request.method == 'POST':
        if not has_device:
            device = TOTPDevice.objects.create(user=user, name='default')
            device.save()
            messages.success(request, 'Authentification à deux facteurs activée.')
        return redirect('accounts:profile')

    context = {
        'has_device': has_device,
        'page_title': 'Authentification à deux facteurs'
    }

    return render(request, 'accounts/setup_two_factor.html', context)


@login_required
def two_factor_qr(request):
    """Générer le QR code pour l'authentification à deux facteurs"""
    from django_otp.plugins.otp_totp.models import TOTPDevice
    import qrcode
    import qrcode.image.svg
    from io import BytesIO
    import base64

    try:
        device = TOTPDevice.objects.get(user=request.user, name='default')

        # Générer le QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(device.config_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()

        return JsonResponse({'qr_code': f'data:image/png;base64,{qr_code_data}'})
    except TOTPDevice.DoesNotExist:
        return JsonResponse({'error': 'Aucun dispositif trouvé'}, status=404)


def social_account_connected(request):
    """Callback après connexion d'un compte social"""
    messages.success(request, 'Votre compte social a été connecté avec succès.')
    return redirect('accounts:profile')


def social_account_disconnected(request):
    """Callback après déconnexion d'un compte social"""
    messages.success(request, 'Votre compte social a été déconnecté avec succès.')
    return redirect('accounts:profile')

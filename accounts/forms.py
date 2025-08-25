from django import forms
from allauth.account.forms import SignupForm, LoginForm
from django.contrib.auth import get_user_model
from .models import Shopper

User = get_user_model()


class CustomSignupForm(SignupForm):
    """Formulaire d'inscription personnalisé pour Django Allauth"""

    first_name = forms.CharField(
        max_length=30,
        label='Prénom',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre prénom',
            'required': True
        })
    )

    last_name = forms.CharField(
        max_length=30,
        label='Nom',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom',
            'required': True
        })
    )

    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label='Numéro de téléphone',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre numéro de téléphone (optionnel)',
            'type': 'tel'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personnaliser les champs existants
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'votre.email@exemple.com'
        })

        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe sécurisé'
        })

        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmez votre mot de passe'
        })

    def save(self, request):
        # Sauvegarder l'utilisateur avec Allauth
        user = super().save(request)

        # Ajouter les informations supplémentaires
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if self.cleaned_data.get('phone_number'):
            user.phone_number = self.cleaned_data['phone_number']

        user.save()

        return user


class CustomLoginForm(LoginForm):
    """Formulaire de connexion personnalisé pour Django Allauth"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personnaliser les champs
        self.fields['login'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Votre adresse email',
            'autofocus': True
        })

        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Votre mot de passe'
        })

        # Modifier les labels
        self.fields['login'].label = 'Email'
        self.fields['password'].label = 'Mot de passe'


class ProfileUpdateForm(forms.ModelForm):
    """Formulaire de mise à jour du profil utilisateur"""

    class Meta:
        model = Shopper
        fields = ['first_name', 'last_name', 'phone_number', 'birth_date', 'newsletter_subscription']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre numéro de téléphone',
                'type': 'tel'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'newsletter_subscription': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'phone_number': 'Numéro de téléphone',
            'birth_date': 'Date de naissance',
            'newsletter_subscription': 'S\'abonner à la newsletter'
        }


class ContactForm(forms.Form):
    """Formulaire de contact"""

    name = forms.CharField(
        max_length=100,
        label='Nom complet',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom complet'
        })
    )

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre.email@exemple.com'
        })
    )

    subject = forms.CharField(
        max_length=200,
        label='Sujet',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sujet de votre message'
        })
    )

    message = forms.CharField(
        label='Message',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Votre message...',
            'rows': 5
        })
    )

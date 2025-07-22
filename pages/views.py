from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json


def about_view(request):
    """Vue pour la page À propos inspirée de Rhode Skin"""
    context = {
        "page_title": "Notre Histoire",
        "meta_description": "Découvrez l'histoire de yee, notre philosophie et notre engagement pour une mode durable et accessible.",
    }
    return render(request, "pages/about.html", context)


def contact_view(request):
    """Vue pour la page Contact inspirée de Rhode Skin"""
    if request.method == "POST":
        # Récupération des données du formulaire
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        order_number = request.POST.get("order_number", "")
        contact_reason = request.POST.get("contact_reason")
        message = request.POST.get("message")

        # Validation basique
        if not all([first_name, last_name, email, contact_reason, message]):
            messages.error(
                request, "Tous les champs obligatoires doivent être remplis."
            )
            return render(request, "pages/contact.html")

        # Formatage du message email
        email_subject = f"Contact YEE - {contact_reason}"
        email_body = f"""
        Nouveau message de contact reçu:
        
        Nom: {first_name} {last_name}
        Email: {email}
        Numéro de commande: {order_number if order_number else 'N/A'}
        Raison du contact: {contact_reason}
        
        Message:
        {message}
        """

        try:
            # Envoi de l'email (configurez vos paramètres SMTP dans settings.py)
            send_mail(
                email_subject,
                email_body,
                email,  # From email
                ["hello@yee-fashion.com"],  # To email
                fail_silently=False,
            )

            # Email de confirmation au client
            confirmation_subject = "Votre message a été reçu - YEE"
            confirmation_body = f"""
            Bonjour {first_name},
            
            Nous avons bien reçu votre message concernant: {contact_reason}
            
            Notre équipe vous répondra dans les 2 jours ouvrables.
            
            Merci de votre confiance,
            L'équipe YEE
            """

            send_mail(
                confirmation_subject,
                confirmation_body,
                "hello@yee-fashion.com",
                [email],
                fail_silently=True,
            )

            messages.success(
                request,
                "Votre message a été envoyé avec succès ! Nous vous répondrons dans les 2 jours ouvrables.",
            )
            return redirect("pages:contact")

        except Exception as e:
            messages.error(
                request,
                "Une erreur est survenue lors de l'envoi de votre message. Veuillez réessayer.",
            )
            return render(request, "pages/contact.html")

    context = {
        "page_title": "Contactez-nous",
        "meta_description": "Contactez l'équipe YEE pour toutes vos questions sur nos produits, commandes et services.",
    }
    return render(request, "pages/contact.html", context)


def faq_view(request):
    """Vue pour la page FAQ"""
    faq_data = [
        {
            "category": "Commandes et Livraison",
            "questions": [
                {
                    "question": "Quels sont les délais de livraison ?",
                    "answer": "Les commandes sont généralement livrées sous 3-5 jours ouvrables en France métropolitaine.",
                },
                {
                    "question": "La livraison est-elle gratuite ?",
                    "answer": "Oui, la livraison est gratuite pour toute commande de 70€ et plus en France métropolitaine.",
                },
                {
                    "question": "Puis-je suivre ma commande ?",
                    "answer": "Oui, vous recevrez un email avec un numéro de suivi dès l'expédition de votre commande.",
                },
            ],
        },
        {
            "category": "Retours et Échanges",
            "questions": [
                {
                    "question": "Quelle est votre politique de retour ?",
                    "answer": "Vous avez 30 jours pour retourner vos articles dans leur état d'origine avec les étiquettes.",
                },
                {
                    "question": "Les retours sont-ils gratuits ?",
                    "answer": "Oui, les retours sont gratuits en France métropolitaine via notre étiquette prépayée.",
                },
                {
                    "question": "Comment puis-je échanger un article ?",
                    "answer": "Contactez notre service client pour organiser un échange. Nous vous guiderons dans le processus.",
                },
            ],
        },
        {
            "category": "Produits et Tailles",
            "questions": [
                {
                    "question": "Comment choisir ma taille ?",
                    "answer": "Consultez notre guide des tailles sur chaque page produit. En cas de doute, contactez-nous.",
                },
                {
                    "question": "Vos vêtements sont-ils durables ?",
                    "answer": "Oui, nous utilisons uniquement des matériaux certifiés durables et de haute qualité.",
                },
                {
                    "question": "Comment entretenir mes vêtements YEE ?",
                    "answer": "Chaque produit inclut des instructions d'entretien détaillées pour préserver sa qualité.",
                },
            ],
        },
    ]

    context = {
        "page_title": "Questions Fréquentes",
        "meta_description": "Trouvez rapidement les réponses à vos questions sur YEE.",
        "faq_data": faq_data,
    }
    return render(request, "pages/faq.html", context)


@require_http_methods(["POST"])
def newsletter_signup(request):
    """Vue AJAX pour l'inscription à la newsletter"""
    try:
        data = json.loads(request.body)
        email = data.get("email")

        if not email:
            return JsonResponse({"success": False, "message": "Email requis"})

        # Ici vous pouvez ajouter la logique pour sauvegarder l'email
        # dans votre base de données ou service de newsletter

        # Pour l'instant, on simule juste un succès
        return JsonResponse(
            {
                "success": True,
                "message": "Merci ! Vous êtes maintenant inscrit à notre newsletter.",
            }
        )

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": "Une erreur est survenue. Veuillez réessayer.",
            }
        )

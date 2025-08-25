from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.template import Template, Context
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .email_template_models import EmailTemplate, EmailTestSend
from .email_services import EmailService
import json


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Interface d'administration pour les templates d'emails"""

    list_display = (
        'template_badge',
        'subject_display',
        'is_active_badge',
        'last_modified',
        'actions_links'
    )

    list_filter = ('is_active', 'name', 'last_modified')
    search_fields = ('subject', 'html_content')

    fieldsets = (
        ('Configuration', {
            'fields': ('name', 'subject', 'is_active')
        }),
        ('Contenu HTML', {
            'fields': ('html_content',),
            'classes': ('wide',)
        }),
        ('Informations', {
            'fields': ('last_modified', 'created_at'),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ('last_modified', 'created_at')

    actions = ['load_templates_from_files', 'preview_templates', 'activate_templates']

    def template_badge(self, obj):
        colors = {
            'welcome': '#28a745',
            'order_confirmation': '#007bff',
            'order_status_update': '#ffc107',
            'newsletter': '#17a2b8'
        }
        icons = {
            'welcome': '🎉',
            'order_confirmation': '📋',
            'order_status_update': '📦',
            'newsletter': '📰'
        }

        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">'
            '{} {}</span>',
            colors.get(obj.name, '#6c757d'),
            icons.get(obj.name, '📧'),
            obj.get_name_display()
        )

    template_badge.short_description = "📧 Type"

    def subject_display(self, obj):
        return format_html(
            '<strong style="color: #333;">{}</strong>',
            obj.subject[:60] + '...' if len(obj.subject) > 60 else obj.subject
        )

    subject_display.short_description = "Sujet"

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">✅ Actif</span>'
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">❌ Inactif</span>'
        )

    is_active_badge.short_description = "Statut"

    def actions_links(self, obj):
        return format_html(
            '<a href="/admin/accounts/emailtemplate/{}/preview/" '
            'style="background: #17a2b8; color: white; padding: 2px 6px; '
            'border-radius: 4px; text-decoration: none; font-size: 10px; margin-right: 5px;">'
            '👁️ Aperçu</a>'
            '<a href="/admin/accounts/emailtemplate/{}/test/" '
            'style="background: #ffc107; color: black; padding: 2px 6px; '
            'border-radius: 4px; text-decoration: none; font-size: 10px;">'
            '🧪 Test</a>',
            obj.pk, obj.pk
        )

    actions_links.short_description = "Actions"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:template_id>/preview/', self.admin_site.admin_view(self.preview_template), name='emailtemplate_preview'),
            path('<int:template_id>/test/', self.admin_site.admin_view(self.test_template), name='emailtemplate_test'),
            path('load-from-files/', self.admin_site.admin_view(self.load_from_files_view), name='emailtemplate_load'),
        ]
        return custom_urls + urls

    def preview_template(self, request, template_id):
        """Vue d'aperçu du template"""
        template = EmailTemplate.objects.get(pk=template_id)

        # Données d'exemple pour l'aperçu
        sample_data = {
            'welcome': {
                'shopper': {'first_name': 'John', 'email': 'john@exemple.com'},
                'site_name': 'YEE Codes',
                'website_url': 'https://y-e-e.tech'
            },
            'order_confirmation': {
                'shopper': {'first_name': 'John', 'email': 'john@exemple.com'},
                'order': {'id': '12345', 'total': '29.99'},
                'items': [{'name': 'Produit Test', 'quantity': 1, 'price': '29.99'}],
                'site_name': 'YEE Codes'
            },
            'order_status_update': {
                'shopper': {'first_name': 'John'},
                'order': {'id': '12345'},
                'new_status': 'Expédié',
                'site_name': 'YEE Codes'
            },
            'newsletter': {
                'shopper': {'first_name': 'John'},
                'content': '<h2>Nouvelle promotion !</h2><p>Découvrez nos dernières offres...</p>',
                'subject': 'Newsletter Test',
                'site_name': 'YEE Codes'
            }
        }

        try:
            django_template = Template(template.html_content)
            context_data = sample_data.get(template.name, {})
            rendered_content = django_template.render(Context(context_data))

            return HttpResponse(rendered_content, content_type='text/html')
        except Exception as e:
            return HttpResponse(f"<h1>Erreur de rendu</h1><p>{str(e)}</p>", status=400)

    def test_template(self, request, template_id):
        """Vue pour tester l'envoi du template"""
        template = EmailTemplate.objects.get(pk=template_id)

        if request.method == 'POST':
            test_email = request.POST.get('test_email')
            if test_email:
                try:
                    # Créer un test d'envoi
                    test_send = EmailTestSend.objects.create(
                        template=template,
                        test_email=test_email,
                        test_data={}
                    )

                    # Envoyer l'email de test
                    success = self._send_test_email(template, test_email)

                    test_send.success = success
                    test_send.sent_at = timezone.now()
                    if not success:
                        test_send.error_message = "Erreur lors de l'envoi"
                    test_send.save()

                    if success:
                        messages.success(request, f"Email de test envoyé à {test_email}")
                    else:
                        messages.error(request, "Erreur lors de l'envoi du test")

                except Exception as e:
                    messages.error(request, f"Erreur: {str(e)}")
            else:
                messages.error(request, "Veuillez saisir une adresse email")

        context = {
            'template': template,
            'title': f'Test du template: {template.get_name_display()}',
            'opts': self.model._meta,
        }

        return render(request, 'admin/email_template_test.html', context)

    def _send_test_email(self, template, test_email):
        """Envoie un email de test"""
        try:
            from django.utils import timezone

            # Données d'exemple selon le type de template
            sample_data = {
                'welcome': {
                    'shopper': type('obj', (object,), {
                        'first_name': 'Test',
                        'email': test_email
                    })(),
                    'site_name': 'YEE Codes',
                    'website_url': 'https://y-e-e.tech'
                },
                'newsletter': {
                    'shopper': type('obj', (object,), {'first_name': 'Test'})(),
                    'content': '<h2>Test Newsletter</h2><p>Ceci est un test de newsletter.</p>',
                    'subject': template.subject,
                    'site_name': 'YEE Codes'
                }
            }

            context_data = sample_data.get(template.name, {})

            # Utiliser le service d'email approprié
            if template.name == 'welcome' and hasattr(EmailService, 'send_welcome_email'):
                return EmailService.send_welcome_email(context_data.get('shopper'))
            elif template.name == 'newsletter':
                shopper_obj = context_data.get('shopper')
                shopper_obj.email = test_email
                sent_count, error_count = EmailService.send_newsletter(
                    template.subject,
                    context_data.get('content'),
                    [shopper_obj]
                )
                return sent_count > 0
            else:
                # Envoi générique
                email = EmailMultiAlternatives(
                    subject=f"[TEST] {template.subject}",
                    body="Version test du template",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[test_email]
                )

                django_template = Template(template.html_content)
                rendered_content = django_template.render(Context(context_data))
                email.attach_alternative(rendered_content, "text/html")

                email.send()
                return True

        except Exception as e:
            print(f"Erreur envoi test: {e}")
            return False

    def load_from_files_view(self, request):
        """Vue pour charger les templates depuis les fichiers"""
        if request.method == 'POST':
            try:
                EmailTemplate.load_from_files()
                messages.success(request, "Templates chargés depuis les fichiers avec succès!")
            except Exception as e:
                messages.error(request, f"Erreur lors du chargement: {str(e)}")

        return redirect('admin:accounts_emailtemplate_changelist')

    def load_templates_from_files(self, request, queryset):
        """Action pour charger les templates depuis les fichiers"""
        try:
            EmailTemplate.load_from_files()
            self.message_user(request, "Templates rechargés depuis les fichiers avec succès!")
        except Exception as e:
            self.message_user(request, f"Erreur: {str(e)}", level=messages.ERROR)

    load_templates_from_files.short_description = "🔄 Recharger depuis les fichiers"

    def activate_templates(self, request, queryset):
        """Active les templates sélectionnés"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} template(s) activé(s)")

    activate_templates.short_description = "✅ Activer les templates"


@admin.register(EmailTestSend)
class EmailTestSendAdmin(admin.ModelAdmin):
    """Interface d'administration pour les tests d'emails"""

    list_display = (
        'template_info',
        'test_email',
        'success_badge',
        'sent_at'
    )

    list_filter = ('success', 'template__name', 'sent_at')
    search_fields = ('test_email', 'error_message')
    readonly_fields = ('sent_at', 'success', 'error_message')

    def template_info(self, obj):
        return format_html(
            '<strong>{}</strong>',
            obj.template.get_name_display()
        )

    template_info.short_description = "Template"

    def success_badge(self, obj):
        if obj.success:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">✅ Succès</span>'
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">❌ Échec</span>'
        )

    success_badge.short_description = "Résultat"

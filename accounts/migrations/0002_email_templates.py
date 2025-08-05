# Generated manually for email templates

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),  # Ajustez selon votre dernière migration
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('welcome', '🎉 Email de bienvenue'), ('order_confirmation', '📋 Confirmation de commande'), ('order_status_update', '📦 Mise à jour de statut'), ('newsletter', '📰 Newsletter')], max_length=50, unique=True, verbose_name='Type de template')),
                ('subject', models.CharField(help_text='Le sujet par défaut pour ce type d\'email', max_length=200, verbose_name='Sujet de l\'email')),
                ('html_content', models.TextField(help_text='Le contenu HTML du template. Utilisez {{ variable }} pour les variables dynamiques.', verbose_name='Contenu HTML')),
                ('is_active', models.BooleanField(default=True, help_text='Désactiver temporairement ce template', verbose_name='Template actif')),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': "Template d'email",
                'verbose_name_plural': "Templates d'emails",
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='EmailTestSend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_email', models.EmailField(help_text="L'adresse email où envoyer le test", max_length=254, verbose_name='Email de test')),
                ('test_data', models.JSONField(blank=True, default=dict, help_text='Variables JSON pour tester le template', verbose_name='Données de test')),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('success', models.BooleanField(default=False)),
                ('error_message', models.TextField(blank=True)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.emailtemplate', verbose_name='Template à tester')),
            ],
            options={
                'verbose_name': "Test d'email",
                'verbose_name_plural': "Tests d'emails",
                'ordering': ['-sent_at'],
            },
        ),
    ]

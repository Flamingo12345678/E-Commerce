# Generated by Django 5.2.4 on 2025-07-14 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="shopper",
            options={
                "ordering": ["-date_joined"],
                "verbose_name": "Client",
                "verbose_name_plural": "Clients",
            },
        ),
        migrations.AddField(
            model_name="shopper",
            name="address",
            field=models.TextField(blank=True, verbose_name="Adresse"),
        ),
        migrations.AddField(
            model_name="shopper",
            name="birth_date",
            field=models.DateField(
                blank=True, null=True, verbose_name="Date de naissance"
            ),
        ),
        migrations.AddField(
            model_name="shopper",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, null=True, verbose_name="Date de création"
            ),
        ),
        migrations.AddField(
            model_name="shopper",
            name="newsletter_subscription",
            field=models.BooleanField(
                default=False, verbose_name="Abonnement à la newsletter"
            ),
        ),
        migrations.AddField(
            model_name="shopper",
            name="phone_number",
            field=models.CharField(
                blank=True, max_length=20, verbose_name="Numéro de téléphone"
            ),
        ),
        migrations.AddField(
            model_name="shopper",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True, null=True, verbose_name="Dernière mise à jour"
            ),
        ),
    ]

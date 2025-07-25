# Generated by Django 5.2.4 on 2025-07-18 21:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CDNResource",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(help_text="Nom de la ressource", max_length=100),
                ),
                (
                    "resource_type",
                    models.CharField(
                        choices=[
                            ("css", "CSS"),
                            ("js", "JavaScript"),
                            ("font", "Font"),
                            ("icon", "Icon"),
                        ],
                        help_text="Type de ressource",
                        max_length=20,
                    ),
                ),
                ("cdn_url", models.URLField(help_text="URL du CDN")),
                (
                    "local_fallback",
                    models.CharField(
                        blank=True, help_text="Chemin local de fallback", max_length=200
                    ),
                ),
                (
                    "version",
                    models.CharField(
                        blank=True, help_text="Version de la ressource", max_length=20
                    ),
                ),
                (
                    "is_critical",
                    models.BooleanField(
                        default=False,
                        help_text="Ressource critique (chargement prioritaire)",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, help_text="Ressource active"),
                ),
                (
                    "load_order",
                    models.PositiveIntegerField(
                        default=0, help_text="Ordre de chargement (0 = premier)"
                    ),
                ),
            ],
            options={
                "verbose_name": "Ressource CDN",
                "verbose_name_plural": "Ressources CDN",
                "ordering": ["load_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="SiteConfiguration",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "site_name",
                    models.CharField(
                        default="YEE", help_text="Nom du site", max_length=100
                    ),
                ),
                (
                    "site_title",
                    models.CharField(
                        default="YEE E-Commerce",
                        help_text="Titre affiché dans le navigateur",
                        max_length=200,
                    ),
                ),
                (
                    "site_tagline",
                    models.CharField(
                        default="One of EVERYTHING really GOOD.",
                        help_text="Slogan principal",
                        max_length=200,
                    ),
                ),
                (
                    "site_description",
                    models.TextField(
                        default="Mode de qualité pour tous - Découvrez notre sélection",
                        help_text="Description du site",
                    ),
                ),
                (
                    "contact_email",
                    models.EmailField(
                        default="hello@yee-fashion.com",
                        help_text="Email de contact principal",
                        max_length=254,
                    ),
                ),
                (
                    "support_email",
                    models.EmailField(
                        default="support@yee-commerce.com",
                        help_text="Email de support",
                        max_length=254,
                    ),
                ),
                (
                    "company_address",
                    models.TextField(
                        default="123 Fashion Street\n75001 Paris, France",
                        help_text="Adresse de l'entreprise",
                    ),
                ),
                (
                    "company_phone",
                    models.CharField(
                        default="+33 1 23 45 67 89",
                        help_text="Téléphone de l'entreprise",
                        max_length=20,
                    ),
                ),
                (
                    "support_hours",
                    models.CharField(
                        default="Lun-Ven 9h-17h PST",
                        help_text="Horaires de support",
                        max_length=100,
                    ),
                ),
                (
                    "instagram_url",
                    models.URLField(blank=True, help_text="URL Instagram"),
                ),
                ("youtube_url", models.URLField(blank=True, help_text="URL YouTube")),
                ("tiktok_url", models.URLField(blank=True, help_text="URL TikTok")),
                (
                    "privacy_policy_url",
                    models.URLField(
                        blank=True, help_text="URL politique de confidentialité"
                    ),
                ),
                (
                    "terms_url",
                    models.URLField(
                        blank=True, help_text="URL conditions d'utilisation"
                    ),
                ),
                (
                    "accessibility_url",
                    models.URLField(blank=True, help_text="URL accessibilité"),
                ),
                (
                    "footer_newsletter_title",
                    models.CharField(
                        default="Rejoignez-nous pour un style sans effort.",
                        help_text="Titre de la newsletter",
                        max_length=200,
                    ),
                ),
                (
                    "footer_newsletter_description",
                    models.TextField(
                        default="Illuminez votre boîte mail avec nos conseils, astuces et contenus exclusifs de notre équipe.",
                        help_text="Description de la newsletter",
                    ),
                ),
                (
                    "copyright_text",
                    models.CharField(
                        default="© YEE 2025",
                        help_text="Texte de copyright",
                        max_length=100,
                    ),
                ),
                (
                    "meta_keywords",
                    models.TextField(
                        default="mode, vêtements, qualité, style, fashion",
                        help_text="Mots-clés SEO généraux",
                    ),
                ),
                (
                    "cdn_base_url",
                    models.URLField(
                        blank=True, help_text="URL de base pour le CDN (optionnel)"
                    ),
                ),
                (
                    "google_analytics_id",
                    models.CharField(
                        blank=True,
                        help_text="ID Google Analytics (ex: GA-XXXXX)",
                        max_length=20,
                    ),
                ),
                (
                    "products_per_page",
                    models.PositiveIntegerField(
                        default=12, help_text="Nombre de produits par page"
                    ),
                ),
                (
                    "featured_products_count",
                    models.PositiveIntegerField(
                        default=8, help_text="Nombre de produits vedettes à afficher"
                    ),
                ),
                (
                    "free_shipping_threshold",
                    models.DecimalField(
                        decimal_places=2,
                        default=50.0,
                        help_text="Montant minimum pour livraison gratuite",
                        max_digits=10,
                    ),
                ),
                (
                    "standard_shipping_cost",
                    models.DecimalField(
                        decimal_places=2,
                        default=4.99,
                        help_text="Coût de livraison standard",
                        max_digits=10,
                    ),
                ),
                (
                    "express_shipping_cost",
                    models.DecimalField(
                        decimal_places=2,
                        default=9.99,
                        help_text="Coût de livraison express",
                        max_digits=10,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "is_active",
                    models.BooleanField(default=True, help_text="Configuration active"),
                ),
            ],
            options={
                "verbose_name": "Configuration du site",
                "verbose_name_plural": "Configurations du site",
            },
        ),
    ]

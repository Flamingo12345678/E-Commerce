"""
URL configuration for shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from shop import settings
from django.views.generic import RedirectView
from store.views import index
from accounts.newsletter_admin import add_newsletter_admin_links
from accounts.admin import ShopperAdmin


# Ajouter les URLs personnalisées du dashboard de notifications à l'admin
admin.site.index_template = "admin/custom_index.html"

urlpatterns = [
    # Admin avec URLs personnalisées pour notifications
    path("admin/", admin.site.urls),
    # URLs du dashboard de notifications (accessible via l'admin)
    path(
        "admin/notifications/",
        include(
            [
                path(
                    "dashboard/",
                    ShopperAdmin.notifications_dashboard,
                    name="admin_notifications_dashboard",
                ),
                path(
                    "compose/",
                    ShopperAdmin.compose_newsletter,
                    name="admin_compose_newsletter",
                ),
                path(
                    "subscribers/",
                    ShopperAdmin.view_subscribers,
                    name="admin_view_subscribers",
                ),
                path(
                    "stats/", ShopperAdmin.email_stats, name="admin_email_stats"
                ),
            ]
        ),
    ),
    # Redirection de /admin vers /admin/
    path("admin", RedirectView.as_view(url="/admin/", permanent=True)),
    path("", index, name="index"),
    # Include URLs from accounts app (authentication + payment) - URLs PERSONNALISÉES PRIORITAIRES
    path("accounts/", include("accounts.urls", namespace="accounts")),
    # Include Django Allauth URLs sous accounts/ (pour login, signup, etc.) - APRÈS vos URLs personnalisées
    path("accounts/", include("allauth.urls")),
    # Include URLs from pages app (static pages)
    path("pages/", include("pages.urls")),
    # Include URLs from store app
    path("store/", include("store.urls")),
    # Redirections pour compatibilité avec les anciennes URLs
    path("login/", RedirectView.as_view(url="/accounts/login/", permanent=True)),
    path("signup/", RedirectView.as_view(url="/accounts/signup/", permanent=True)),
    path("logout/", RedirectView.as_view(url="/accounts/logout/", permanent=True)),
    path("profile/", RedirectView.as_view(url="/accounts/profile/", permanent=True)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

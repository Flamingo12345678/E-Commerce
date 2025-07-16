from django.contrib import admin
from django.conf import settings

# Personnalisation de l'interface admin
admin.site.site_header = getattr(
    settings, "ADMIN_SITE_HEADER", "YEE E-Commerce - Administration"
)
admin.site.site_title = getattr(settings, "ADMIN_SITE_TITLE", "YEE Admin")
admin.site.index_title = getattr(
    settings, "ADMIN_INDEX_TITLE", "Tableau de bord administrateur"
)

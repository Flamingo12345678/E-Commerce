from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
    path("about/", views.about_view, name="about"),
    path("contact/", views.contact_view, name="contact"),
    path("faq/", views.faq_view, name="faq"),
    path("newsletter/signup/", views.newsletter_signup, name="newsletter_signup"),
]

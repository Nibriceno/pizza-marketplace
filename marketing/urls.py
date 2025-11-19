from django.urls import path
from .views import email_list
from . import views

urlpatterns = [
     path("email-list/", views.email_list, name="email_list"),
]

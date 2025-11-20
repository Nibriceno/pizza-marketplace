from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.conf import settings
from vendor.models import Vendor
from product.models import Product

class Command(BaseCommand):
    help = "Envía promociones personalizadas por comuna y preferencias"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # IDs de usuarios vendedores
        vendedores_ids = Vendor.objects.values_list("created_by_id", flat=True)

        # USUARIOS NORMALES (no vendedores)
        usuarios = User.objects.exclude(
            id__in=vendedores_ids
        ).exclude(
            email=""
        ).exclude(
            email__isnull=True
        )

        enviados = 0

        for user in usuarios:
            profile = user.profile
            comuna = profile.comuna
            prefs = profile.preferences.all()

            producto = None

            # Productos en la comuna del usuario
            productos_comuna = Product.objects.filter(
                vendor__created_by__profile__comuna=comuna
            )

            # Filtrar por preferencias si existen
            if prefs.exists():
                productos_pref = productos_comuna.filter(preferences__in=prefs).distinct()

                if productos_pref.exists():
                    producto = productos_pref.order_by("-added_date").first()
                elif productos_comuna.exists():
                    producto = productos_comuna.order_by("-added_date").first()
            else:
                if productos_comuna.exists():
                    producto = productos_comuna.order_by("-added_date").first()

            # Si no hay nada → Fallback global
            if not producto:
                producto = Product.objects.order_by("-added_date").first()

            # Render HTML
            if producto:
                asunto = f"🔥 Oferta especial en {comuna}: {producto.title}"
                html = render_to_string("marketing/oferta_comuna.html", {
                    "user": user,
                    "producto": producto,
                    "comuna": comuna,
                    "preferences": prefs,
                    "site_url": "https://nicolasbriceno.pythonanywhere.com",
                    "image_url": f"https://nicolasbriceno.pythonanywhere.com{producto.image.url}" if producto.image else "",
                })
            else:
                asunto = "🍕 Descubre nuestras pizzas disponibles"
                html = render_to_string("marketing/oferta_generica.html", {
                    "user": user,
                    "site_url": "https://nicolasbriceno.pythonanywhere.com",
                })

            # Enviar correo
            msg = EmailMultiAlternatives(
                subject=asunto,
                body="",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            msg.attach_alternative(html, "text/html")
            msg.send()

            enviados += 1

        self.stdout.write(self.style.SUCCESS(f"Correos enviados: {enviados}"))


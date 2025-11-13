from django.shortcuts import render, redirect
from django.http import JsonResponse
from product.models import Product
from .models import Country
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from analytics.utils import log_event
from django.contrib import messages



#  Página principal
def frontpage(request):
    countries = Country.objects.all()
    selected_country = request.GET.get('country')

    # 🧠 Si el usuario selecciona un país, guardarlo en la sesión
    if selected_country:
        request.session['selected_country'] = selected_country
    else:
        selected_country = request.session.get('selected_country')

    newest_products = Product.objects.all().order_by('-id')

    # 🔒 Si el usuario NO está logueado
    if not request.user.is_authenticated:
        if selected_country:
            try:
                country = Country.objects.get(id=selected_country)
                newest_products = newest_products.filter(
                    vendor__created_by__profile__country=country
                )
            except Country.DoesNotExist:
                newest_products = []
        else:
            newest_products = []
    else:
        # 🔓 Si el usuario está logueado y tiene país
        if hasattr(request.user, 'profile') and request.user.profile.country:
            user_country = request.user.profile.country
            newest_products = newest_products.filter(
                vendor__created_by__profile__country=user_country
            )
            selected_country = user_country.id
            request.session['selected_country'] = user_country.id  # guarda en sesión también

    newest_products = newest_products[:8]

    context = {
        'countries': countries,
        'selected_country': selected_country,
        'newest_products': newest_products,
    }

    return render(request, 'core/frontpage.html', context)


# 📞 Página de contacto
def contactpage(request):
    return render(request, 'core/contact.html')


# ☎️ Obtener prefijo telefónico por país (JSON)
def get_country_phone_code(request, pk):
    country = Country.objects.get(pk=pk)
    return JsonResponse({'phone_code': country.phone_code})


# 🔁 Redirección al home de products
def home(request):
    return redirect('product:home')


@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_landing(request):
    return render(request, 'core/admin_landing.html')


class CustomLoginView(LoginView):
    template_name = 'vendor/login.html'

    def form_valid(self, form):
        """Cuando el login es correcto"""
        response = super().form_valid(form)
        user = self.request.user

        # ✅ Mensaje visual de bienvenida
        messages.success(self.request, f"👋 Bienvenido {user.username}")

        # 📊 Registrar el evento de inicio de sesión
        log_event(
            self.request,
            action=f"👤 Usuario inició sesión ({user.username})",
            page="login",
            extra_data={"method": self.request.method}
        )
        return response

    def form_invalid(self, form):
        """Cuando el login falla"""
        messages.error(self.request, "⚠️ Usuario o contraseña incorrectos. Inténtalo nuevamente.")
        return super().form_invalid(form)

    def get_success_url(self):
        """Redirección condicional según tipo de usuario"""
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return reverse_lazy('core:admin_landing')
        elif hasattr(user, 'vendor'):
            return reverse_lazy('vendor:vendor-admin')
        else:
            return reverse_lazy('core:home')


def custom_404(request, exception=None):
    """Página personalizada para errores 404"""
    return render(request, 'core/404.html', status=404)


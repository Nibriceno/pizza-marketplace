from django.shortcuts import render, redirect
from django.http import JsonResponse
from product.models import Product
from .models import Country

# 🏠 Página principal
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

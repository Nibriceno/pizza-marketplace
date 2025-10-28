from django.shortcuts import render
from product.models import Product
from django.http import JsonResponse
from .models import Country
# Create your views here.

from django.shortcuts import render
from product.models import Product

def frontpage(request):
    newest_products = Product.objects.all().order_by('-id')

    # 🧭 Filtrar productos por país si el usuario está logueado
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.country:
        user_country = request.user.profile.country
        newest_products = newest_products.filter(vendor__country=user_country)

    # 🪄 Limitar a 8 productos recientes
    newest_products = newest_products[:8]

    context = {
        'newest_products': newest_products,
    }
    return render(request, 'core/frontpage.html', context)



def contactpage(request):
    return render(request, 'core/contact.html')




def get_country_phone_code(request, pk):
    country = Country.objects.get(pk=pk)
    return JsonResponse({'phone_code': country.phone_code})


from django.shortcuts import redirect

def home(request):
    return redirect('product:home')  # 👈 redirige automáticamente al home de products

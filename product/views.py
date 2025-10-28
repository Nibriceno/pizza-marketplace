import random  # To get random products from the database
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Q
from product.models import Product
from .models import Category, Product
from .forms import AddToCartForm
from cart.cart import Cart


def product(request, category_slug, product_slug):
    cart = Cart(request)
    product = get_object_or_404(Product, category__slug=category_slug, slug=product_slug)

    # 🧭 Verificamos si el usuario tiene país asignado
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.country:
        user_country = request.user.profile.country

        # 🛡️ Si el país del producto no coincide con el del usuario → redirigimos
        if product.vendor.country != user_country:
            messages.warning(
                request,
                f"🚫 Esta pizza no está disponible en tu país ({user_country.name})."
            )
            return redirect('product:category', category_slug=category_slug)

    else:
        # Si no hay país o no está logueado, también redirigimos
        messages.warning(
            request,
            "Debes iniciar sesión para ver este producto."
        )
        return redirect('vendor:login')  # O 'core:home' si prefieres

    # 🪙 Obtenemos moneda y símbolo
    currency_symbol = product.vendor.country.currency_symbol or ''
    currency_code = product.vendor.country.currency or ''

    # 🛒 Agregar al carrito
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            cart.add(product_id=product.id, quantity=quantity, update_quantity=False)
            messages.success(request, "El producto fue agregado al carrito.")
            return redirect('product:product', category_slug=category_slug, product_slug=product_slug)
    else:
        form = AddToCartForm()

    # 🧭 Productos similares
    similar_products = list(product.category.products.exclude(id=product.id))
    if len(similar_products) >= 4:
        similar_products = random.sample(similar_products, 4)

    context = {
        'product': product,
        'similar_products': similar_products,
        'form': form,
        'currency_symbol': currency_symbol,
        'currency_code': currency_code,
    }

    return render(request, 'product/product.html', context)


# ✅ Vista para mostrar una categoría de productos
def category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = category.products.all()

    # 🧭 Si el usuario está logueado y tiene país
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.country:
        user_country = request.user.profile.country
        products = products.filter(vendor__country=user_country)

    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'product/category.html', context)


# ✅ Vista para búsqueda de productos
def search(request):
    query = request.GET.get('query', '')
    products = Product.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    )

    # 🧭 Filtrar por país si el usuario está logueado
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.country:
        user_country = request.user.profile.country
        products = products.filter(vendor__country=user_country)

    return render(request, 'product/search.html', {
        'products': products,
        'query': query
    })

from product.models import Product

def home(request):
    newest_products = Product.objects.all().order_by('-id')

    # 🧭 Filtrar por país si el usuario está logueado
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.country:
        user_country = request.user.profile.country
        newest_products = newest_products.filter(vendor__country=user_country)

    # 🪄 Limitar a 12 productos recientes
    newest_products = newest_products[:12]

    return render(request, 'core/frontpage.html', {
        'newest_products': newest_products
    })



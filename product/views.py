import random
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Q
from product.models import Product
from .models import Category, Product
from .forms import AddToCartForm
from cart.cart import Cart
from core.models import Country


def product(request, category_slug, product_slug):
    from analytics.utils import log_event  # 🔹 Import local para evitar dependencias circulares

    cart = Cart(request)
    product = get_object_or_404(Product, category__slug=category_slug, slug=product_slug)

    # 🧭 Verificamos país del usuario
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.country:
        user_country = request.user.profile.country
        if product.vendor.country != user_country:
            messages.warning(request, f"🚫 Esta pizza no está disponible en tu país ({user_country.name}).")
            return redirect('product:category', category_slug=category_slug)
    else:
        messages.warning(request, "Debes iniciar sesión para ver este producto.")
        return redirect('vendor:login')

    # ⚙️ Evita duplicar logs tras agregar al carrito
    current_view = f"view_{product.id}"
    last_view = request.session.get("last_product_view")

    # 👀 Solo loguear si es un GET normal y no viene de un POST anterior
    if request.method == "GET" and last_view != current_view:
        log_event(
            request,
            action=f"👀 Vio producto '{product.title}'",
            page="product/detail",
            product_id=product.id,
            extra_data={"precio": product.price}  # ✅ solo precio (no hay cantidad aún)
        )
        request.session["last_product_view"] = current_view

    # 🪙 Moneda
    currency_symbol = product.vendor.country.currency_symbol or ''
    currency_code = product.vendor.country.currency or ''

    # 🛒 Agregar al carrito
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            cart.add(product_id=product.id, quantity=quantity, update_quantity=False)
            messages.success(request, "El producto fue agregado al carrito.")

            # 🧠 Log: el usuario seleccionó este producto (con detalles)
            log_event(
                request,
                action=f"🖱️ Seleccionó producto '{product.title}' (x{quantity})",
                page="product/detail",
                product_id=product.id,
                extra_data={
                    "precio": product.price,
                    "cantidad": quantity,
                    "total": product.price * quantity
                }
            )

            # 🧩 Marcar que el siguiente GET proviene de este POST
            request.session["last_product_view"] = current_view

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


def category(request, category_slug):
    from analytics.utils import log_event

    category = get_object_or_404(Category, slug=category_slug)
    products = []

    # 🔓 Si el usuario está logueado → usar su país
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.country:
        user_country = request.user.profile.country
        products = Product.objects.filter(
            category=category,
            vendor__created_by__profile__country=user_country
        )
    else:
        country_id = request.session.get('selected_country')
        if country_id:
            try:
                country = Country.objects.get(id=country_id)
                products = Product.objects.filter(
                    category=category,
                    vendor__created_by__profile__country=country
                )
            except Country.DoesNotExist:
                products = []

    # 🧠 Log: el usuario visitó esta categoría
    log_event(
        request,
        action=f"📂 Entró a la categoría '{category.title}'",
        page="product/category",
        extra_data={"productos_disponibles": len(products)}
    )

    return render(request, 'product/category.html', {
        'category': category,
        'products': products,
    })


def search(request):
    from analytics.utils import log_event

    query = request.GET.get('query', '')
    products = Product.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    )

    # 🧭 Filtrar por país si el usuario está logueado
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.country:
        user_country = request.user.profile.country
        products = products.filter(vendor__country=user_country)

    # 🧠 Log: búsqueda
    if query.strip():
        log_event(
            request,
            action=f"🔍 Buscó '{query}'",
            page="product/search",
            extra_data={"resultados": products.count()}
        )

    return render(request, 'product/search.html', {
        'products': products,
        'query': query
    })


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

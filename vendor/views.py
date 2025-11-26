from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify  
from .forms import SignUpForm, ProductForm
from .models import Vendor, Profile
from product.models import Product
from .models import Preference
from django.contrib import messages
from order.models import  Order
from offers.models import Offer
from offers.forms import OfferForm



#Registro de cliente
def register_customer_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('core:admin_landing')  
            else:
                return redirect("vendor:select-preferences")



    else:
        form = SignUpForm()

    # Personalización visual
    for field_name, field in form.fields.items():
        field.widget.attrs['class'] = 'input'
        placeholders = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'country': 'Selecciona tu país',
            'phone': '+56 9 12345678',
            'address': 'Dirección',
            'zipcode': 'Código postal',
            'password1': 'Contraseña',
            'password2': 'Confirmar contraseña'
        }
        if field_name in placeholders:
            field.widget.attrs['placeholder'] = placeholders[field_name]

    return render(request, 'vendor/become_customer.html', {'form': form})


# Registro de vendedor
def register_vendor_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        store_name = request.POST.get('store_name', '')

        if form.is_valid():
            user = form.save()
            login(request, user)

            profile = Profile.objects.get(user=user)
            country = profile.country

            Vendor.objects.create(
                name=store_name if store_name else user.username,
                created_by=user,
                country=country
            )

            # Redirección condicional
            if user.is_staff or user.is_superuser:
                return redirect('core:admin_landing')
            else:
                return redirect('core:home')
    else:
        form = SignUpForm()

    # Personalización visual
    for field_name, field in form.fields.items():
        field.widget.attrs['class'] = 'input'
        placeholders = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'country': 'Selecciona tu país',
            'phone': '+56 9 12345678',
            'address': 'Dirección',
            'zipcode': 'Código postal',
            'password1': 'Contraseña',
            'password2': 'Confirmar contraseña'
        }
        if field_name in placeholders:
            field.widget.attrs['placeholder'] = placeholders[field_name]

    return render(request, 'vendor/become_vendor.html', {'form': form})


@login_required
def vendor_admin(request):
    context = {}

    if hasattr(request.user, 'vendor'):
        vendor = request.user.vendor
        products = vendor.products.all()
        orders = vendor.orders.all()

        for order in orders:
            order.vendor_amount = 0
            order.vendor_paid_amount = 0
            order.fully_paid = True

            for item in order.items.all():
                if item.vendor == vendor:

                    # 🔥 PRECIO FINAL CON OFERTA
                    price = item.product.get_final_price()
                    total_item = item.quantity * price

                    if item.vendor_paid:
                        order.vendor_paid_amount += total_item
                    else:
                        order.vendor_amount += total_item
                        order.fully_paid = False

        context['is_vendor'] = True
        context['vendor'] = vendor
        context['products'] = products
        context['orders'] = orders

    else:
        context['is_vendor'] = False
        context['username'] = request.user.username

    return render(request, 'vendor/vendor_admin.html', context)

# Agregar producto
@login_required

def add_product(request):
    if not hasattr(request.user, 'vendor'):
        return redirect('core:home')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user.vendor
            product.slug = slugify(product.title)
            product.save()

            # ⭐ MUY IMPORTANTE — GUARDA LAS PREFERENCIAS ⭐
            form.save_m2m()

            return redirect('vendor:profile')

    else:
        form = ProductForm()

    return render(request, 'vendor/add_product.html', {'form': form})



#Eliminar producto
@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor)
    product.delete()
    return redirect('vendor:profile')


#Editar información del vendedor
@login_required
def edit_vendor(request):
    if not hasattr(request.user, 'vendor'):
        return redirect('core:home')

    vendor = request.user.vendor

    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')

        if name:
            vendor.name = name
        if email:
            vendor.created_by.email = email
            vendor.created_by.save()

        vendor.save()
        return redirect('vendor:vendor-admin')

    return render(request, 'vendor/edit_vendor.html', {'vendor': vendor})


#Lista de vendedores
def vendors(request):
    vendors = Vendor.objects.all()
    return render(request, 'vendor/vendors.html', {'vendors': vendors})


#Perfil de un vendedor
def vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    return render(request, 'vendor/vendor.html', {'vendor': vendor})


@login_required
def profile_view(request):
    user = request.user

    # PERFIL DEL VENDEDOR
    if hasattr(user, "vendor"):
        vendor = user.vendor

        # Todos los productos del vendedor
        products = vendor.products.all()

        # Todos los items vendidos por este vendedor
        items = vendor.items.select_related("order", "product").all()

        # Todos los pedidos donde participa este vendedor
        orders = (
             Order.objects.filter(items__vendor=vendor)
            .distinct()
            .order_by('-id')
        )

        return render(request, "vendor/vendor_profile.html", {
            "vendor": vendor,
            "products": products,
            "orders": orders,
            "items": items,
        })


    # Si es cliente → perfil cliente
    profile = user.profile
    preferences = Preference.objects.all()
    selected_ids = list(profile.preferences.values_list("id", flat=True))

    # 🔥 SI HAY POST → GUARDAR PREFERENCIAS
    if request.method == "POST":
        selected = request.POST.getlist("preferences")
        profile.preferences.set(selected)
        profile.save()

        messages.success(request, "Preferencias actualizadas correctamente 🍕")
        return redirect("vendor:profile")

    return render(request, "vendor/customer_profile.html", {
        "profile": profile,
        "username": user.username,
        "email": user.email,
        "preferences": preferences,
        "selected_ids": selected_ids,
    })


@login_required
def select_preferences(request):
    profile = request.user.profile
    preferences = Preference.objects.all()

    # Si ya tiene preferencias → saltar onboarding
    if profile.preferences.exists():
        return redirect('home')

    if request.method == "POST":
        selected = request.POST.getlist("preferences")
        profile.preferences.set(selected)
        profile.save()
        return redirect('core:home')

    return render(request, "vendor/select_preferences.html", {
        "preferences": preferences
    })


@login_required
def edit_preferences(request):
    profile = request.user.profile
    preferences = Preference.objects.all()

    if request.method == "POST":
        selected = request.POST.getlist("preferences")
        profile.preferences.set(selected)
        profile.save()
        return redirect("vendor:edit-preferences")

    return render(request, "vendor/edit_preferences.html", {
        "preferences": preferences,
        "selected": profile.preferences.all()
    })
@login_required
def edit_offer(request, product_id):
    if not hasattr(request.user, "vendor"):
        return redirect("core:home")

    product = get_object_or_404(Product, id=product_id, vendor=request.user.vendor)

    # Si el producto tiene oferta → editar
    try:
        offer = product.offer
    except Offer.DoesNotExist:
        offer = None

    if request.method == "POST":
        form = OfferForm(request.POST, instance=offer)

        if form.is_valid():
            new_offer = form.save(commit=False)
            new_offer.product = product
            new_offer.save()

            messages.success(request, "Oferta actualizada correctamente 🎉")
            return redirect("vendor:profile")


        else:
            print("FORM ERRORS:", form.errors)

    else:
        form = OfferForm(instance=offer)

    return render(request, "vendor/edit_offer.html", {
        "product": product,
        "form": form,
        "offer": offer,
    })
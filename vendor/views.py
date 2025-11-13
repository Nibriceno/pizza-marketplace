from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify  
from .forms import SignUpForm, ProductForm
from .models import Vendor, Profile
from product.models import Product


# 🧍 Registro de cliente
def register_customer_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('core:admin_landing')  
            else:
                return redirect('core:home')

    else:
        form = SignUpForm()

    # 🎨 Personalización visual
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


# 🏪 Registro de vendedor
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

            # 🔁 Redirección condicional
            if user.is_staff or user.is_superuser:
                return redirect('core:admin_landing')
            else:
                return redirect('core:home')
    else:
        form = SignUpForm()

    # 🎨 Personalización visual
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


#  Panel del vendedor
@login_required
def vendor_admin(request):
    context = {}

    # Si es vendedor
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
                    if item.vendor_paid:
                        order.vendor_paid_amount += item.get_total_price()
                    else:
                        order.vendor_amount += item.get_total_price()
                        order.fully_paid = False

        context['is_vendor'] = True
        context['vendor'] = vendor
        context['products'] = products
        context['orders'] = orders

    #  Si es usuario normal
    else:
        context['is_vendor'] = False
        context['username'] = request.user.username

    return render(request, 'vendor/vendor_admin.html', context)

#  Agregar producto
@login_required
def add_product(request):
    if not hasattr(request.user, 'vendor'):
        return redirect('core:home')  # seguridad extra

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user.vendor
            product.slug = slugify(product.title)
            product.save()
            return redirect('vendor:vendor-admin')
    else:
        form = ProductForm()

    return render(request, 'vendor/add_product.html', {'form': form})


#  Eliminar producto
@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor)
    product.delete()
    return redirect('vendor:vendor-admin')


#  Editar información del vendedor
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


#  Lista de vendedores
def vendors(request):
    vendors = Vendor.objects.all()
    return render(request, 'vendor/vendors.html', {'vendors': vendors})


#  Perfil de un vendedor
def vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    return render(request, 'vendor/vendor.html', {'vendor': vendor})



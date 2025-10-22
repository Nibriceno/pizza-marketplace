from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from .models import Vendor
from product.models import Product
from .forms import ProductForm

# Converting Title into Slug
from django.utils.text import slugify

# Create your views here.


def become_vendor(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
    else:
        form = UserCreationForm()

    # 🪄 Agregar estilos y traducciones directamente desde la vista
    for field_name, field in form.fields.items():
        # Clase CSS para que todos tengan el mismo estilo (Bulma)
        field.widget.attrs['class'] = 'input'

        # Traducciones y placeholders personalizados
        if field_name == 'username':
            field.label = 'Nombre de usuario'
            field.widget.attrs['placeholder'] = 'Ingresa tu nombre de usuario'
        elif field_name == 'password1':
            field.label = 'Contraseña'
            field.widget.attrs['placeholder'] = 'Ingresa tu contraseña'
        elif field_name == 'password2':
            field.label = 'Confirmar contraseña'
            field.widget.attrs['placeholder'] = 'Confirma tu contraseña'

    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            vendor = Vendor.objects.create(name=user.username, created_by=user)
            return redirect('core:home')

    return render(request, 'vendor/become_vendor.html', {'form': form})

@login_required
def vendor_admin(request):
    vendor = request.user.vendor
    products = vendor.products.all()
    orders = vendor.orders.all()
    for order in orders:
        order.vendor_amount = 0
        order.vendor_paid_amount = 0
        order.fully_paid = True

        for item in order.items.all():
            if item.vendor == request.user.vendor:
                if item.vendor_paid:
                    order.vendor_paid_amount += item.get_total_price()
                else:
                    order.vendor_amount += item.get_total_price()
                    order.fully_paid = False


    return render(request, 'vendor/vendor_admin.html', {'vendor': vendor, 'products': products, 'orders': orders})

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            product = form.save(commit=False) # Because we have not given vendor yet
            product.vendor = request.user.vendor
            product.slug = slugify(product.title)
            product.save() #finally save

            return redirect('vendor:vendor-admin')

    else:
        form = ProductForm

    return render(request, 'vendor/add_product.html', {'form': form})

@login_required
def delete_product(request, pk):
    """
    Permite a un vendedor eliminar uno de sus productos.
    Solo se borra si el producto pertenece al usuario logueado.
    """
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor)
    product.delete()
    return redirect('vendor:vendor-admin')


@login_required
def edit_vendor(request):
    vendor = request.user.vendor

    if request.method == 'POST':
        name  = request.POST.get('name', '')
        email = request.POST.get('email', '')

        if name:
            vendor.created_by.email = email
            vendor.created_by.save()

            vendor.name = name
            vendor.save

            return redirect('vendor:vendor-admin')

    return render(request, 'vendor/edit_vendor.html', {'vendor': vendor})


def vendors(request):
    vendors = Vendor.objects.all()
    return render(request, 'vendor/vendors.html', {'vendors': vendors})

def vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    return render(request, 'vendor/vendor.html', {'vendor': vendor})



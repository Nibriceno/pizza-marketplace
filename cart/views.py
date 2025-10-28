import mercadopago
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .cart import Cart
from .forms import CheckoutForm
from order.utilities import checkout, notify_vendor, notify_customer

@login_required
def cart_detail(request):
    cart = Cart(request)

    #  Autocompletar datos desde el perfil (si existe)
    initial_data = {}
    if request.user.is_authenticated:
        initial_data['first_name'] = request.user.first_name or ''
        initial_data['last_name'] = request.user.last_name or ''
        initial_data['email'] = request.user.email or ''
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            initial_data['phone'] = getattr(profile, 'phone', '') or ''
            initial_data['address'] = getattr(profile, 'address', '') or ''
            initial_data['zipcode'] = getattr(profile, 'zipcode', '') or ''
            initial_data['place'] = getattr(profile, 'place', '') or ''

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                #  Datos del pedido
                total = float(cart.get_total_cost())
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                email = form.cleaned_data['email']
                phone = form.cleaned_data['phone']
                address = form.cleaned_data['address']
                zipcode = form.cleaned_data['zipcode']
                place = form.cleaned_data['place']

                #  Validar campos mínimos requeridos
                required_fields = [first_name, last_name, email, phone, address, zipcode, place]
                if any(f.strip() == '' for f in required_fields):
                    messages.error(request, "Por favor completa todos los campos obligatorios antes de continuar.")
                    return redirect('cart:cart')

                #  Inicializar Mercado Pago
                mp = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

                preference_data = {
                    "items": [
                        {
                            "title": f"Pedido de {first_name} {last_name}",
                            "quantity": 1,
                            "unit_price": total,
                            "currency_id": "CLP",
                        }
                    ],
                    "payer": {
                        "name": first_name,
                        "surname": last_name,
                        "email": email,
                    },
                    "back_urls": {
                        "success": "https://nicolasbriceno.pythonanywhere.com/cart/success/",
                        "failure": "https://nicolasbriceno.pythonanywhere.com/cart/failure/",
                        "pending": "https://nicolasbriceno.pythonanywhere.com/cart/pending/",
                    },
                    "auto_return": "approved",
                    "binary_mode": True,
                }

                result = mp.preference().create(preference_data)
                preference = result.get("response", {})
                init_point = preference.get("init_point")

                if not init_point:
                    messages.error(request, "No se pudo generar el enlace de pago. Intenta nuevamente.")
                    return redirect('cart:cart')

                #  Registrar orden
                order = checkout(
                    request,
                    first_name,
                    last_name,
                    email,
                    phone,
                    address,
                    zipcode,
                    place,
                    cart.get_total_cost()
                )

                #  Limpiar carrito
                cart.clear()

                #  Notificar (opcional)
                # notify_customer(order)
                # notify_vendor(order)

                return redirect(init_point)

            except Exception as e:
                print(" Error en Mercado Pago:", e)
                messages.error(request, f"Hubo un problema al procesar el pago: {str(e)}")
                return redirect('cart:cart')
        else:
            messages.error(request, "Por favor corrige los errores del formulario.")
            return redirect('cart:cart')

    else:
        #  Instanciar el formulario con los datos iniciales si existen
        form = CheckoutForm(initial=initial_data)

    # ⚙️ Acciones del carrito (eliminar / cambiar cantidad)
    remove_from_cart = request.GET.get('remove_from_cart', '')
    change_quantity = request.GET.get('change_quantity', '')
    quantity = request.GET.get('quantity', 0)

    if remove_from_cart:
        cart.remove(remove_from_cart)
        return redirect('cart:cart')

    if change_quantity:
        cart.add(change_quantity, quantity, True)
        return redirect('cart:cart')

    return render(request, 'cart/cart.html', {
        'form': form,
        'cart': cart,
        'mp_public_key': settings.MERCADOPAGO_PUBLIC_KEY
    })



#  Vista de éxito
def success(request):
    messages.success(request, "¡El pago se completó exitosamente!")
    return render(request, 'cart/success.html')


#  Vista de fallo
def failure(request):
    messages.error(request, "El pago fue rechazado o cancelado.")
    return redirect('cart:cart')


#  Vista de pago pendiente
def pending(request):
    messages.info(request, "El pago está pendiente de confirmación.")
    return redirect('cart:cart')

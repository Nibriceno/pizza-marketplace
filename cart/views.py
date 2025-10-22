import mercadopago  # pip install mercadopago
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from .cart import Cart
from .forms import CheckoutForm
from order.utilities import checkout, notify_vendor, notify_customer


# 🛒 Detalle del carrito y checkout
def cart_detail(request):
    cart = Cart(request)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                # 🔑 Inicializar Mercado Pago con tu token (sandbox)
                mp = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

                # 🧾 Datos del pedido
                total = float(cart.get_total_cost())
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                email = form.cleaned_data['email']
                phone = form.cleaned_data['phone']
                address = form.cleaned_data['address']
                zipcode = form.cleaned_data['zipcode']
                place = form.cleaned_data['place']

                total = float(cart.get_total_cost())

                # 🧠 Validar nombre y apellido
                if not first_name or not last_name:
                    messages.error(request, "Debes ingresar tu nombre y apellido para continuar con el pago.")
                    return redirect('cart:cart')

                # 💳 Crear la preferencia de pago
                preference_data = {
                    "items": [
                        {
                            "title": f"Pedido de {first_name} {last_name}",
                            "quantity": 1,
                            "unit_price": 10000,  # Asegúrate de convertirlo a entero
                            "currency_id": "CLP",
                        }
                    ],
                    
                    "payer": {
                        "name": first_name,
                        "surname": last_name,
                        "email": email,
                    },
                    "back_urls": {
                        "success": "https://nonfimbriate-usha-aerobically.ngrok-free.dev/cart/success/",
                        "failure": "https://nonfimbriate-usha-aerobically.ngrok-free.dev/cart/failure/",
                        "pending": "https://nonfimbriate-usha-aerobically.ngrok-free.dev/cart/pending/",
                    },
                    "auto_return": "approved",
                    # 📡 Recomendado en producción para recibir notificaciones
                    # "notification_url": "https://TU-DOMINIO/webhooks/mercadopago/",
                }

                # 🚀 Crear preferencia y mostrar resultado en consola
                result = mp.preference().create(preference_data)
                print("🔍 Mercado Pago RESULT:", result)

                preference = result.get("response", {})

                # Usar siempre la URL sandbox para pruebas
                init_point = preference.get("sandbox_init_point")

                if not init_point:
                    messages.error(request, "No se pudo generar el enlace de pago (ver consola).")
                    return redirect('cart:cart')

                # 💾 Registrar orden antes de redirigir
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

                # 🧹 Limpiar carrito
                cart.clear()

                # 📩 Enviar notificaciones
                # notify_customer(order)
                # notify_vendor(order)

                # 🌐 Redirigir al checkout de Mercado Pago
                return redirect(init_point)

            except Exception as e:
                print("Error en Mercado Pago:", e)
                messages.error(request, f"Hubo un problema al procesar el pago: {str(e)}")
                return redirect('cart:cart')
    else:
        form = CheckoutForm()

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
        'mp_public_key': settings.MERCADOPAGO_PUBLIC_KEY
    })


# ✅ Vista de éxito
def success(request):
    messages.success(request, "¡El pago se completó exitosamente!")
    return render(request, 'cart/success.html')


# ⚠️ Vista de fallo
def failure(request):
    messages.error(request, "El pago fue rechazado o cancelado.")
    return redirect('cart:cart')


# 🕒 Vista de pago pendiente
def pending(request):
    messages.info(request, "El pago está pendiente de confirmación.")
    return redirect('cart:cart')

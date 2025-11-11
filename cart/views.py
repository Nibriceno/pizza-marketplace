import json
import mercadopago
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .cart import Cart
from .forms import CheckoutForm
from order.utilities import checkout, notify_customer, notify_vendor
from botapi.models import TempCart
from order.models import Order

# 🧠 Importamos el logger de analytics
from analytics.utils import log_event


# 🛒 DETALLE DEL CARRITO
@login_required
def cart_detail(request):
    cart = Cart(request)

    try:
        # 🧩 Acciones rápidas (agregar, eliminar, cambiar cantidad)
        remove_from_cart = request.GET.get('remove_from_cart', '')
        change_quantity = request.GET.get('change_quantity', '')
        quantity = request.GET.get('quantity', 0)
        add_product = request.GET.get('add_product', '')

        if remove_from_cart:
            cart.remove(remove_from_cart)
            log_event(
                request,
                action=f"❌ Eliminó producto {remove_from_cart} del carrito",
                page="cart/remove",
                extra_data={"product_id": remove_from_cart}
            )
            return redirect('cart:cart')

        if change_quantity:
            try:
                quantity = int(quantity)
            except ValueError:
                quantity = 1
            if str(change_quantity) in cart.cart:
                cart.add(change_quantity, quantity, update_quantity=False)
            else:
                cart.add(change_quantity, quantity, update_quantity=True)

            log_event(
                request,
                action=f"🔄 Cambió cantidad del producto {change_quantity} a {quantity}",
                page="cart/change",
                extra_data={"product_id": change_quantity, "new_quantity": quantity}
            )
            return redirect('cart:cart')

        if add_product:
            cart.add(add_product, 1)
            log_event(
                request,
                action=f"🛒 Agregó producto {add_product} al carrito",
                page="cart/add",
                extra_data={"product_id": add_product, "quantity": 1}
            )
            return redirect('cart:cart')

        # Datos iniciales del usuario
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                "first_name": request.user.first_name or "",
                "last_name": request.user.last_name or "",
                "email": request.user.email or "",
            }
            if hasattr(request.user, "profile"):
                profile = request.user.profile
                initial_data.update({
                    "phone": getattr(profile, "phone", "") or "",
                    "address": getattr(profile, "address", "") or "",
                    "zipcode": getattr(profile, "zipcode", "") or "",
                    "place": getattr(profile, "place", "") or "",
                })

        # 🧾 Checkout
        if request.method == "POST":
            form = CheckoutForm(request.POST)
            if form.is_valid():
                try:
                    total = float(cart.get_total_cost())
                    data = form.cleaned_data

                    required_fields = [
                        data["first_name"], data["last_name"], data["email"],
                        data["phone"], data["address"], data["zipcode"], data["place"]
                    ]
                    if any(f.strip() == "" for f in required_fields):
                        messages.error(request, "Por favor completa todos los campos antes de continuar.")
                        log_event(
                            request,
                            action="Formulario incompleto en checkout",
                            page="cart/checkout",
                            extra_data={"form_data": data},
                        )
                        return redirect("cart:cart")

                    # ✅ Crear orden antes de ir a MP
                    order = checkout(
                        request,
                        first_name=data["first_name"],
                        last_name=data["last_name"],
                        email=data["email"],
                        phone=data["phone"],
                        address=data["address"],
                        zipcode=data["zipcode"],
                        place=data["place"],
                        amount=total,
                        send_email=False,
                    )

                    log_event(
                        request,
                        action=f"💳 Inició proceso de pago para orden #{order.id}",
                        page="cart/checkout",
                        extra_data={"order_id": order.id, "monto_total": total}
                    )

                    # Usamos la URL dinámica para Mercado Pago
                    base_url = settings.BASE_URL  # Usamos BASE_URL configurada

                    mp = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                    preference_data = {
                        "items": [
                            {
                                "title": item["product"].title,
                                "quantity": item["quantity"],
                                "unit_price": float(item["product"].price),
                                "currency_id": "CLP",
                            }
                            for item in cart
                        ],
                        "payer": {
                            "name": data["first_name"],
                            "surname": data["last_name"],
                            "email": data["email"],
                        },
                        "back_urls": {
                            "success": f"{base_url}/cart/success/",  # URL dinámica
                            "failure": f"{base_url}/cart/failure/",
                            "pending": f"{base_url}/cart/pending/",
                        },
                        "auto_return": "approved",
                        "binary_mode": True,
                        "notification_url": f"{base_url}/cart/webhook/",  # URL dinámica para webhook
                        "external_reference": str(order.id),
                    }

                    result = mp.preference().create(preference_data)
                    init_point = result.get("response", {}).get("init_point")

                    if not init_point:
                        messages.error(request, "No se pudo generar el enlace de pago.")
                        log_event(
                            request,
                            action="Error al generar init_point de Mercado Pago",
                            page="cart/checkout",
                            extra_data={"order_id": order.id, "total": total},
                        )
                        return redirect("cart:cart")

                    return redirect(init_point)

                except Exception as e:
                    print("❌ Error al generar pago:", e)
                    messages.error(request, f"Error al procesar el pago: {e}")
                    log_event(
                        request,
                        action="Error en generación de pago",
                        page="cart/checkout",
                        extra_data={"error": str(e), "cart_total": cart.get_total_cost()},
                    )
                    return redirect("cart:cart")

            messages.error(request, "Formulario inválido.")
            log_event(
                request,
                action="Formulario inválido en checkout",
                page="cart/checkout",
                extra_data={"raw_post_data": request.POST.dict()},
            )
            return redirect("cart:cart")

        else:
            form = CheckoutForm(initial=initial_data)

        # 👀 Log de acceso al carrito
        log_event(
            request,
            action="👀 Entró al detalle del carrito",
            page="cart/detail",
            extra_data={"total_items": len(cart), "total_cost": cart.get_total_cost()}
        )

        return render(request, "cart/cart.html", {
            "form": form,
            "cart": cart,
            "mp_public_key": settings.MERCADOPAGO_PUBLIC_KEY,
        })

    except Exception as e:
        log_event(
            request,
            action="Error general en cart_detail",
            page="cart/detail",
            extra_data={"error": str(e)} 
        )
        raise


# ✅ ÉXITO DE COMPRA
@login_required
def success(request):
    cart = Cart(request)
    order = Order.objects.filter(email=request.user.email).order_by("-id").first()
    cart.clear()
    messages.success(request, "✅ Tu pago fue procesado. Te enviamos la confirmación a tu correo.")
    log_event(request, f"✅ Pago exitoso en orden #{order.id if order else 'desconocida'}", page="cart/success")
    return render(request, "cart/success.html", {"order": order})


# ❌ PAGO FALLIDO
def failure(request):
    messages.error(request, "❌ El pago fue rechazado o cancelado.")
    log_event(request, "❌ Pago fallido o cancelado", status="error", page="cart/failure")
    return redirect("cart:cart")


# ⏳ PAGO PENDIENTE
def pending(request):
    messages.info(request, "🕓 El pago está pendiente de confirmación.")
    log_event(request, "🕓 Pago pendiente de confirmación", page="cart/pending")
    return redirect("cart:cart")


# 🧠 BOT: CARRITO TEMPORAL
@login_required
def checkout_start(request):
    token = request.GET.get("cart_token")
    if not token:
        messages.error(request, "Carrito no encontrado.")
        log_event(request, "Carrito temporal no encontrado (sin token)", status="error", page="cart/checkout_start")
        return redirect("cart:cart")

    try:
        temp_cart = TempCart.objects.get(token=token)
    except TempCart.DoesNotExist:
        messages.error(request, "El carrito ya expiró o no existe.")
        log_event(request, "Carrito temporal expirado o inexistente", status="error", page="cart/checkout_start")
        return redirect("cart:cart")

    cart = Cart(request)
    for item in temp_cart.items.all():
        cart.add(item.product.id, item.quantity)

    temp_cart.delete()
    log_event(request, "🧠 Checkout iniciado desde bot", page="cart/checkout_start")
    return redirect("cart:cart")



@csrf_exempt
def webhook(request):
    """Marca órdenes como pagadas cuando Mercado Pago confirma el pago."""
    try:
        payload_raw = request.body.decode("utf-8") or "{}"
        payload = json.loads(payload_raw)
        print("📩 Webhook recibido:", json.dumps(payload, indent=4))

        # 🧠 Log inicial del webhook recibido
        log_event(
            request,
            action="📩 Webhook recibido desde Mercado Pago",
            page="cart/webhook",
            extra_data={"payload_preview": payload_raw[:300]}  # los primeros 300 caracteres
        )

        topic = payload.get("type") or request.GET.get("topic")
        payment_id = (
            payload.get("data", {}).get("id")
            or request.GET.get("data.id")
            or request.GET.get("id")
        )

        if not payment_id:
            log_event(
                request,
                action="⚠️ Webhook ignorado (sin payment_id)",
                page="cart/webhook",
                extra_data={"payload": payload}
            )
            return JsonResponse({"status": "ignored"}, status=200)

        if topic and topic != "payment":
            log_event(
                request,
                action=f"ℹ️ Webhook ignorado (topic={topic})",
                page="cart/webhook",
                extra_data={"topic": topic}
            )
            return JsonResponse({"status": "ignored"}, status=200)

        mp = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        payment_info = mp.payment().get(payment_id)
        data = payment_info.get("response", {})
        print("💳 Pago recibido:", json.dumps(data, indent=4))

        if data.get("status") != "approved":
            log_event(
                request,
                action=f"🕓 Pago pendiente o no aprobado",
                page="cart/webhook",
                extra_data={
                    "payment_id": payment_id,
                    "status": data.get("status"),
                    "amount": data.get("transaction_amount")
                }
            )
            return JsonResponse({"status": "pending"}, status=200)

        external_ref = data.get("external_reference")
        if not external_ref:
            log_event(
                request,
                action="⚠️ Webhook sin external_reference",
                page="cart/webhook",
                extra_data={"payment_id": payment_id, "response": data}
            )
            return JsonResponse({"status": "error", "message": "Sin external_reference"}, status=200)

        # Buscar orden creada en checkout
        try:
            order = Order.objects.get(pk=int(external_ref))
        except Order.DoesNotExist:
            log_event(
                request,
                action=f"❌ Orden {external_ref} no encontrada",
                page="cart/webhook",
                extra_data={"payment_id": payment_id, "external_reference": external_ref}
            )
            return JsonResponse({"status": "error", "message": "Orden no encontrada"}, status=200)

        # Evitar duplicados
        if hasattr(order, "paid") and order.paid:
            log_event(
                request,
                action=f"ℹ️ Webhook duplicado: orden #{order.id} ya estaba pagada",
                page="cart/webhook",
                extra_data={"payment_id": payment_id, "status": "duplicado"}
            )
            return JsonResponse({"status": "ok"}, status=200)

        # ✅ Marcar orden como pagada
        order.paid_amount = data.get("transaction_amount", order.paid_amount)
        if hasattr(order, "paid"):
            order.paid = True
        order.save()

        # Enviar correos
        notify_customer(order)
        notify_vendor(order)
        print(f"✅ Orden #{order.id} marcada como pagada y correos enviados.")

        # Log final de éxito
        log_event(
            request,
            action=f"✅ Orden #{order.id} marcada como pagada (Webhook)",
            page="cart/webhook",
            extra_data={
                "payment_id": payment_id,
                "monto": data.get("transaction_amount"),
                "metodo": data.get("payment_type_id"),
                "email_pagador": data.get("payer", {}).get("email"),
                "status": data.get("status_detail")
            }
        )

        return JsonResponse({"status": "ok"}, status=200)

    except Exception as e:
        print("❌ Error en webhook:", e)
        log_event(
            request,
            action="❌ Error general en webhook Mercado Pago",
            page="cart/webhook",
            extra_data={"error": str(e)}
        )
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

from order.models import Order, OrderItem
from product.models import Product
from cart.cart import Cart
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


# =============================
# 📧 EMAIL A VENDEDOR
# =============================
def notify_vendor(order):
    from_email = settings.DEFAULT_FROM_EMAIL

    for vendor in order.vendors.all():
        to_email = vendor.created_by.email
        subject = f'🛒 Nueva orden #{order.id} en tu tienda'
        text_content = f'Hola {vendor.name}, tienes una nueva orden.'
        html = render_to_string(
            'order/email_notify_vendor.html',
            {'order': order, 'vendor': vendor}
        )

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html, 'text/html')
        msg.send()


# =============================
# 📧 EMAIL A CLIENTE
# =============================
def notify_customer(order):
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = order.email

    subject = f'✅ Confirmación de tu orden #{order.id}'
    text_content = 'Gracias por tu pedido 🍕'
    html = render_to_string(
        'order/email_notify_customer.html',
        {'order': order}
    )

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html, 'text/html')
    msg.send()


# =============================
# 🧾 CHECKOUT (100% OFERTAS READY)
# =============================
def checkout(
    request,
    first_name,
    last_name,
    email,
    address,
    zipcode,
    place,
    phone,
    amount,
    send_email=True,
):
    # 1️⃣ Crear Orden
    order = Order.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        address=address,
        zipcode=zipcode,
        place=place,
        phone=phone,
        paid_amount=amount,  # total real pagado
    )

    cart = Cart(request)

    # 2️⃣ Crear OrderItems correctamente
    for item in cart:
        product = item["product"]
        quantity = item["quantity"]

        # Precio final por unidad (ya procesado: % / price fijo)
        unit_price = product.get_final_price()
        original_price = product.price

        # ==========================================================
        # 🧠 CALCULAR PRECIO TOTAL REAL DEL ÍTEM (incluye 2x1)
        # ==========================================================
        if product.active_offer and product.active_offer.is_2x1:
            # 2x1 → unidades efectivamente cobradas
            effective_qty = (quantity // 2) + (quantity % 2)
            total_item_price = effective_qty * unit_price

            # Para reportes
            discount_pct = 50  

        else:
            effective_qty = quantity
            total_item_price = quantity * unit_price

            # porcentaje real si es descuento tradicional
            discount_pct = 0
            if product.active_offer and product.active_offer.discount_percentage:
                discount_pct = product.active_offer.discount_percentage

        # ==========================================================
        # 🧾 GUARDAR EN ORDERITEM
        # ==========================================================
        OrderItem.objects.create(
            order=order,
            product=product,
            vendor=product.vendor,

            # Guardamos *unit_price*, y *effective_qty* para que coincida
            price=unit_price,               # precio final por unidad real
            original_price=original_price,  # precio normal
            discount_percentage=discount_pct,

            quantity=effective_qty,         # UNIDADES REALMENTE PAGADAS
        )

        # relacionar vendor
        order.vendors.add(product.vendor)

    # 3️⃣ Enviar correos
    if send_email:
        try:
            notify_vendor(order)
            notify_customer(order)
        except Exception as e:
            print(f"⚠️ Error enviando notificaciones: {e}")

    return order

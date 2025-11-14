from order.models import Order, OrderItem
from product.models import Product
from cart.cart import Cart
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

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
    #  Crear la orden principal
    order = Order.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        address=address,
        zipcode=zipcode,
        place=place,
        phone=phone,
        paid_amount=amount,
    )

    cart = Cart(request)

    # rear los ítems de la orden
    for item in cart:
        product = item.get("product")
        if not product or not isinstance(product, Product):
            try:
                product = Product.objects.get(pk=item.get("id"))
            except Product.DoesNotExist:
                continue

        OrderItem.objects.create(
            order=order,
            product=product,
            vendor=product.vendor,
            price=product.price,
            quantity=item["quantity"],
        )

        order.vendors.add(product.vendor)

    # Notificar (solo si se indica)
    if send_email:
        try:
            notify_vendor(order)
            notify_customer(order)
        except Exception as e:
            print(f"⚠️ Error enviando notificaciones: {e}")

    return order


def notify_vendor(order):
    from_email = settings.DEFAULT_FROM_EMAIL

    for vendor in order.vendors.all():
        to_email = vendor.created_by.email
        subject = f'🛒 Nueva orden #{order.id} en tu tienda'
        text_content = f'Hola {vendor.name}, tienes una nueva orden para preparar.'
        html_content = render_to_string(
            'order/email_notify_vendor.html',
            {'order': order, 'vendor': vendor}
        )

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, 'text/html')
        msg.send()


def notify_customer(order):
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = order.email

    subject = f'✅ Confirmación de tu orden #{order.id}'
    text_content = 'Gracias por tu pedido 🍕'
    html_content = render_to_string(
        'order/email_notify_customer.html',
        {'order': order}
    )

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()

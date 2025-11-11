import uuid
import json
import secrets
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from product.models import Product
from cart.cart import Cart
from vendor.models import Profile
from botapi.models import TempCart, TempItem, LoginToken


# 🛒 Crear carrito temporal
@csrf_exempt
def create_cart(request):
    """Crea un carrito temporal único por número de teléfono (wa_id) y devuelve su token."""
    phone = request.GET.get("phone")  # viene desde ManyChat como ?phone={{wa_id}}
    token = str(uuid.uuid4())

    # 🧹 Limpia carritos anteriores del mismo número (por seguridad)
    if phone:
        TempCart.objects.filter(phone=phone).delete()
        TempCart.objects.create(token=token, phone=phone)
    else:
        # Fallback si no llega el número (no debería pasar)
        TempCart.objects.create(token=token)

    # 🔁 Respuesta simple y limpia (ManyChat-friendly)
    return JsonResponse({"token": token})


# 📱 Verificar si el usuario ya está registrado
@csrf_exempt
def check_user(request):
    phone = request.GET.get("phone")

    if not phone:
        return JsonResponse({'error': 'No phone provided'}, status=400)

    try:
        user = User.objects.select_related('profile').get(profile__phone=phone)
        return JsonResponse({
            'status': 'registered',
            'name': user.first_name or user.username
        })
    except User.DoesNotExist:
        return JsonResponse({
            'status': 'not_registered',
            'name': ''
        })


# 🍕 Listar pizzas (texto plano compatible con WhatsApp)
@csrf_exempt
def pizzas_cards(request):
    pizzas = Product.objects.all().order_by("id")

    if not pizzas.exists():
        return JsonResponse(
            {"text": "No hay pizzas disponibles en este momento. ¡Vuelve pronto!"},
            safe=False
        )

    generic_image_url = "https://nonfimbriate-usha-aerobically.ngrok-free.dev/media/generics/pizza_generic.jpg"
    message = "🍕 *Estas son nuestras pizzas disponibles:*\n\n"

    for p in pizzas:
        message += (
            f"{generic_image_url}\n"
            f"🧀 *{p.title}*\n"
            f"💵 Precio: *{float(p.price):,.0f} CLP*\n"
            f"➡️ Escribe *{p.id}* para agregar esta pizza al carrito.\n"
            f"──────────────────────────────\n"
        )

    message += "\n🛒 Cuando termines, presiona *ver carrito* para revisar tu pedido."
    return JsonResponse({"text": message}, safe=False)


# ➕ Agregar productos al carrito temporal
@csrf_exempt
def add_to_cart(request):
    """Agrega productos al carrito temporal (acepta solo número, add_ID o JSON)."""
    data = {}

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8")) if request.body else request.POST.dict()
        except Exception:
            data = request.POST.dict()
    elif request.method == "GET":
        data = request.GET.dict()
    else:
        return JsonResponse({
            "status": "error",
            "message": "⚠️ Usa POST o GET para agregar al carrito."
        }, status=200)  # 👈 antes era 405

    print("📦 Datos recibidos en add_to_cart:", data)

    token = data.get("token")
    product_id = data.get("product_id", "") or data.get("message_text", "")
    quantity = data.get("quantity", 1)

    # 🧱 Validación: token obligatorio
    if not token:
        return JsonResponse({
            "status": "error",
            "message": "⚠️ No se encontró el carrito. Escribe *hola* para comenzar un nuevo pedido."
        }, status=200)  # 👈 antes 400

    # Limpieza del product_id
    if isinstance(product_id, str):
        product_id = product_id.strip().replace("add_", "").replace("{", "").replace("}", "").strip()

    # 🧩 Validar que haya un número
    if not product_id:
        return JsonResponse({
            "status": "error",
            "message": "⚠️ Falta el número del producto. Escribe *ver pizzas* para ver los números disponibles."
        }, status=200)  # 👈 antes 400

    # 🧩 Validar que sea número entero
    try:
        product_id = int(product_id)
    except ValueError:
        return JsonResponse({
            "status": "error",
            "message": f"❌ ID inválido: {product_id}. Escribe *ver pizzas* para ver los números disponibles."
        }, status=200)  # 👈 antes 400

    # 🧩 Validar cantidad
    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError
    except Exception:
        quantity = 1

    # 🛒 Buscar carrito válido
    try:
        cart = TempCart.objects.get(token=token)
    except TempCart.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "❌ Carrito no encontrado. Escribe *hola* para crear uno nuevo."
        }, status=200)  # 👈 antes 404

    # 🍕 Buscar producto — aquí reforzamos el mensaje
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": f"🍕 El producto con ID {product_id} no existe. Intenta con otro número o escribe *ver pizzas* para ver la lista."
        }, status=200)  # 👈 antes 404

    # 🧾 Agregar o actualizar item
    item, created = TempItem.objects.get_or_create(
        cart=cart, product=product, defaults={"quantity": quantity}
    )
    if not created:
        item.quantity += quantity
        item.save()

    message = f"✅ {product.title} agregada al carrito (x{item.quantity}) 🛒"
    print("💬 Respuesta enviada a ManyChat:", message)

    return JsonResponse({
        "status": "success",
        "message": message
    }, status=200)  # 👈 mantiene 200



# 👀 Ver contenido del carrito temporal
@csrf_exempt
def view_cart(request):
    """Devuelve el contenido del carrito temporal en formato texto (WhatsApp-friendly)."""
    token = request.GET.get("token")

    if not token:
        return JsonResponse({"text": "❌ Falta el token del carrito."}, status=400)

    try:
        cart = TempCart.objects.get(token=token)
        items = cart.items.select_related("product")

        if not items.exists():
            return JsonResponse({"text": "🛒 Tu carrito está vacío. Escribe *ver pizzas* para seguir comprando."})

        message = "🛒 *Tu carrito actual:*\n\n"
        total = 0

        for i in items:
            subtotal = float(i.subtotal())
            total += subtotal
            message += (
                f"🧀 *{i.product.title}*\n"
                f"Cantidad: {i.quantity}\n"
                f"Subtotal: {subtotal:,.0f} CLP\n"
                f"──────────────────────────────\n"
            )

        message += f"\n💰 *Total: {total:,.0f} CLP*\n\n"
        message += "✅ Presiona *pagar pedido* cuando quieras finalizar tu compra."

        return JsonResponse({
            "status": "success",
            "text": message
        })

    except TempCart.DoesNotExist:
        return JsonResponse({"text": "❌ Carrito no encontrado."}, status=404)


# 💳 Generar link de pago
@csrf_exempt
def pay_order(request):
    """Genera un link de pago con login automático para transferir el carrito temporal."""
    data = request.GET.dict() or request.POST.dict()
    token = data.get("token")
    phone = data.get("phone") or data.get("user_phone")

    if not token:
        return JsonResponse({"status": "error", "message": "⚠️ Falta token del carrito."}, status=400)
    if not phone:
        return JsonResponse({"status": "error", "message": "⚠️ Falta número de teléfono."}, status=400)

    try:
        temp_cart = TempCart.objects.get(token=token)
    except TempCart.DoesNotExist:
        return JsonResponse({"status": "error", "message": "❌ Carrito no encontrado."}, status=404)

    temp_items = TempItem.objects.filter(cart=temp_cart)
    if not temp_items.exists():
        return JsonResponse({"status": "error", "message": "🛒 Tu carrito está vacío."}, status=400)

    try:
        profile = Profile.objects.get(phone=phone)
        user = profile.user
    except Profile.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": f"⚠️ No existe un usuario registrado con el número {phone}."
        }, status=404)

    login_token = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timedelta(minutes=5)
    LoginToken.objects.create(user=user, token=login_token, expires_at=expires_at)

    auto_login_url = (
        f"https://nonfimbriate-usha-aerobically.ngrok-free.dev/"
        f"api/auto-login/{login_token}/?temp_token={token}"
    )

    message = (
        "💳 Tu pedido fue transferido correctamente.\n\n"
        f"👉 Ingresa aquí para ver y pagar tu carrito:\n{auto_login_url}\n\n"
        "Este enlace es válido por 5 minutos ⏳"
    )

    return JsonResponse({
        "status": "success",
        "message": message
    })


# 🔐 Login automático y transferencia de carrito
@csrf_exempt
def auto_login(request, token):
    """Inicia sesión automáticamente y transfiere el carrito temporal al real."""
    record = get_object_or_404(LoginToken, token=token)
    temp_token = request.GET.get("temp_token")

    if not record.is_valid():
        return HttpResponse("⚠️ Token expirado o inválido.", status=403)

    user = record.user
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    request.session.save()
    print(f"✅ Usuario autenticado automáticamente: {user.username}")

    if temp_token:
        try:
            temp_cart = TempCart.objects.get(token=temp_token)
            temp_items = TempItem.objects.filter(cart=temp_cart)

            cart = Cart(request)
            for item in temp_items:
                existing_item = next((i for i in cart.cart.values() if i['id'] == str(item.product.id)), None)
                if existing_item:
                    print(f"🔁 Producto ya en carrito: {item.product.title} — agregando {item.quantity} más.")
                    cart.add(item.product.id, quantity=item.quantity, update_quantity=False)
                else:
                    print(f"🆕 Agregando nuevo producto: {item.product.title} (x{item.quantity})")
                    cart.add(item.product.id, quantity=item.quantity, update_quantity=True)

            cart.save()
            print("🛒 Carrito temporal transferido al carrito real correctamente.")
            temp_items.delete()
            temp_cart.delete()

        except TempCart.DoesNotExist:
            print("⚠️ No se encontró el carrito temporal.")

    print("🔐 Login automático completado, redirigiendo a /cart/")
    return redirect("/cart/")

from .models import UserActionLog
from django.db import DatabaseError

def classify_section(page: str, action: str) -> str:
    """Detecta la sección a partir de la ruta o acción."""
    page = (page or "").lower()
    action = (action or "").lower()

    if "product" in page:
        return "productos"
    elif "category" in page:
        return "categorias"
    elif "cart" in page:
        return "carrito"
    elif "checkout" in page:
        return "checkout"
    elif "error" in action:
        return "errores"
    elif "manychat" in page or "bot" in page or "whatsapp" in page:
        return "bot"
    else:
        return "otros"


def log_event(request, action, page=None, product_id=None, extra_data=None):
    """Registra cualquier evento general del sistema (web, bot, checkout, etc.)."""
    try:
        user = getattr(request, "user", None)
        is_auth = hasattr(user, "is_authenticated") and user.is_authenticated
        user_obj = user if is_auth else None
        user_name = getattr(user, "username", None) if is_auth else "Anónimo"

        section = classify_section(page, action)

        UserActionLog.objects.create(
            user=user_obj,
            user_name=user_name,
            action=action,
            page=page,
            section=section,
            product_id=product_id,
            extra_data=extra_data or {},
        )

    except DatabaseError as e:
        print(f"❌ Error guardando log: {e}")

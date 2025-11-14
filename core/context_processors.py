from product.views import get_active_comuna

def comuna_context(request):
    try:
        comuna = get_active_comuna(request)
    except Exception:
        comuna = None

    return {
        "comuna_activa": comuna
    }



from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from .models import UserActionLog
from vendor.models import Profile
import json
import traceback


# ==========================================================
# 🧭 DASHBOARD PRINCIPAL
# ==========================================================
@staff_member_required

def dashboard(request):
    """Muestra la actividad registrada de usuarios (web + bot + errores)."""
    logs = UserActionLog.objects.all()

    # --- FILTROS ---
    tipo = request.GET.get('tipo', '').strip()
    usuario = request.GET.get('usuario', '').strip()
    fecha = request.GET.get('fecha', '').strip()
    page = request.GET.get('page', '').strip()  # 👈 capturamos bien el parámetro

    # 🧩 Filtro por tipo
    if tipo == 'global':
        logs = logs.filter(action__icontains='ERROR GLOBAL')
    elif tipo == 'error':
        logs = logs.filter(action__icontains='error')
    elif tipo == 'accion':
        logs = logs.exclude(action__icontains='error')

    # 🔍 Filtro por usuario
    if usuario:
        logs = logs.filter(Q(user__username__icontains=usuario) | Q(user_name__icontains=usuario))

    # 📅 Filtro por fecha
    if fecha == 'hoy':
        logs = logs.filter(created_at__date=now().date())

    # 🧭 Filtro por sección (page)
    if page and page != "":  # 👈 verifica que no sea None ni cadena vacía
        logs = logs.filter(page__icontains=page)

    # 🔢 Ordenar y limitar
    logs = logs.order_by('-created_at')[:300]

    # --- CONTADORES ---
    total = UserActionLog.objects.count()
    errores = UserActionLog.objects.filter(action__icontains='error').count()
    usuarios = UserActionLog.objects.exclude(user=None).values('user').distinct().count()

    # --- TOP 5 ACCIONES ---
    mas_comunes = (
        UserActionLog.objects
        .exclude(action__icontains='error')
        .values('action')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    context = {
        'logs': logs,
        'total': total,
        'errores': errores,
        'usuarios': usuarios,
        'mas_comunes': mas_comunes,
        'tipo': tipo,
        'usuario_filtro': usuario,
        'fecha': fecha,
        'page': page,  # 👈 importante para mantener selección del dropdown
    }
    return render(request, 'analytics/dashboard.html', context)

# ==========================================================
# 🤖 ENDPOINT MANYCHAT
# ==========================================================
@csrf_exempt
def manychat_log(request):
    """Recibe datos desde ManyChat y guarda logs o errores automáticamente."""
    if request.method != "POST":
        return JsonResponse({"status": "invalid method"}, status=405)

    try:
        # 🔍 Intentar decodificar el cuerpo como JSON
        try:
            body_raw = request.body.decode("utf-8") if request.body else ""
            data = json.loads(body_raw) if body_raw.strip() else {}
        except json.JSONDecodeError as e:
            # 🚨 JSON inválido: lo registramos igual
            UserActionLog.objects.create(
                user=None,
                user_name="Bot ManyChat",
                action=f"❌ Error JSON inválido desde ManyChat: {str(e)} | Cuerpo: {body_raw[:400]}",
                page="manychat_log",
                product_id=None,
            )
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=200)

        # 📦 Datos recibidos (si el JSON es válido)
        event = data.get("event", "Evento desconocido")
        user_data = data.get("user", {})
        user_name = user_data.get("name", "Anónimo")
        phone = user_data.get("phone")
        source = data.get("source", "ManyChat")
        product_id = data.get("product_id")

        # 🔎 Vincular usuario si existe en Profile
        user_obj = None
        if phone:
            try:
                profile = Profile.objects.filter(phone=phone).select_related("user").first()
                if profile:
                    user_obj = profile.user
            except Exception as e:
                UserActionLog.objects.create(
                    user=None,
                    user_name="Sistema",
                    action=f"⚠️ Error buscando usuario por teléfono: {str(e)}",
                    page="manychat_log"
                )

        # 🧾 Guardar acción correctamente
        UserActionLog.objects.create(
            user=user_obj,
            user_name=user_name,
            page=source,
            action=f"🤖 ManyChat: {event}",
            product_id=product_id,
        )

        return JsonResponse({"status": "ok"}, status=200)

    except Exception as e:
        # 🧨 Cualquier error no previsto (red, server, variables vacías, etc.)
        raw = request.body.decode("utf-8") if request.body else "(sin cuerpo)"
        UserActionLog.objects.create(
            user=None,
            user_name="Bot ManyChat",
            action=f"❌ Error general en manychat_log: {str(e)} | Cuerpo: {raw[:400]}",
            page="manychat_log",
            product_id=None,
        )
        return JsonResponse({"status": "error", "message": str(e)}, status=200)



# ==========================================================
# ⚠️ ENDPOINT DE ERRORES GENERALES DEL BOT (OPCIONAL)
# ==========================================================
@csrf_exempt
def manychat_error_log(request):
    """
    Recibe errores generados por ManyChat (por ejemplo, Invalid JSON, Not Found, o conexión fallida)
    y los guarda automáticamente en UserActionLog.
    """
    try:
        body = request.body.decode("utf-8") if request.body else ""
        UserActionLog.objects.create(
            user=None,
            user_name="Bot ManyChat",
            action=f"❌ Error reportado por ManyChat: {body[:400]}",
            page="ManyChat Error",
        )
        return JsonResponse({"status": "ok"})
    except Exception as e:
        tb = traceback.format_exc()
        print(f"⚠️ No se pudo registrar error de ManyChat: {e}")
        UserActionLog.objects.create(
            user=None,
            user_name="Sistema",
            action=f"⚠️ Falló registro del error del bot: {str(e)} | {tb[:400]}",
            page="manychat_error_log",
        )
        return JsonResponse({"status": "error"}, status=200)

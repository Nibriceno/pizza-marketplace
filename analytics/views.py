from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from .models import UserActionLog
from vendor.models import Profile
from .utils import classify_section
import json


@staff_member_required
def dashboard(request):
    """Dashboard con filtros y colores automáticos."""
    logs = UserActionLog.objects.all()

    # --- FILTROS ---
    tipo = request.GET.get("tipo", "").strip()
    usuario = request.GET.get("usuario", "").strip()
    fecha = request.GET.get("fecha", "").strip()
    page = request.GET.get("page", "").strip()
    section = request.GET.get("section", "").strip()

    # Filtrar por tipo
    if tipo == "global":
        logs = logs.filter(action__icontains="ERROR GLOBAL")
    elif tipo == "error":
        logs = logs.filter(action__icontains="error")
    elif tipo == "accion":
        logs = logs.exclude(action__icontains="error")

    # Filtrar por usuario
    if usuario:
        logs = logs.filter(
            Q(user__username__icontains=usuario) |
            Q(user_name__icontains=usuario)
        )

    # Filtrar por fecha
    if fecha == "hoy":
        logs = logs.filter(timestamp__date=now().date())

    # Filtrar por origen
    if page:
        if page == "web":
            logs = (
                logs.exclude(page__icontains="manychat")
                .exclude(page__icontains="whatsapp")
                .exclude(page__icontains="bot")
                .exclude(action__icontains="manychat")
                .exclude(action__icontains="whatsapp")
                .exclude(action__icontains="bot")
                .exclude(page__icontains="analytics")
            )
        elif page == "manychat":
            logs = logs.filter(
                Q(page__icontains="manychat")
                | Q(action__icontains="manychat")
                | Q(action__icontains="whatsapp")
                | Q(page__icontains="whatsapp")
                | Q(user_name__icontains="bot")
            )
        else:
            logs = logs.filter(page__icontains=page)

    # Filtrar por sección
    if section:
        logs = logs.filter(section__icontains=section)

    logs = logs.order_by("-timestamp")[:400]

    # --- CONTADORES ---
    total = UserActionLog.objects.count()
    errores = UserActionLog.objects.filter(action__icontains="error").count()
    usuarios = UserActionLog.objects.exclude(user=None).values("user").distinct().count()
    mas_comunes = (
        UserActionLog.objects.exclude(action__icontains="error")
        .values("action")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    # --- Asignar color de fila y asegurar sección ---
    for log in logs:
        # Si el registro no tiene sección, asignarla
        if not log.section:
            log.section = classify_section(log.page, log.action)

        action_lower = (log.action or "").lower()
        page_lower = (log.page or "").lower()
        user_lower = (log.user_name or "").lower()

        if any(k in action_lower or k in page_lower or k in user_lower for k in ["manychat", "whatsapp", "bot"]) or log.section == "bot":
            log.row_class = "row-bot"
        elif "error" in action_lower or log.section == "errores":
            log.row_class = "row-error"
        else:
            log.row_class = "row-web"

    context = {
        "logs": logs,
        "total": total,
        "errores": errores,
        "usuarios": usuarios,
        "mas_comunes": mas_comunes,
        "tipo": tipo,
        "usuario_filtro": usuario,
        "fecha": fecha,
        "page": page,
        "section": section,
    }

    return render(request, "analytics/dashboard.html", context)


@csrf_exempt
def manychat_log(request):
    """Recibe datos desde ManyChat y guarda logs o errores automáticamente."""
    if request.method != "POST":
        return JsonResponse({"status": "invalid method"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
        event = data.get("event", "Evento desconocido")
        user_data = data.get("user", {})
        user_name = user_data.get("name", "Anónimo")
        phone = user_data.get("phone")
        product_id = data.get("product_id")

        user_obj = None
        if phone:
            profile = Profile.objects.filter(phone=phone).select_related("user").first()
            if profile:
                user_obj = profile.user

        UserActionLog.objects.create(
            user=user_obj,
            user_name=user_name,
            page="manychat",
            section="bot",
            action=f"🤖 ManyChat: {event}",
            product_id=product_id,
            extra_data={"source": "Bot WhatsApp", "phone": phone},
        )
        return JsonResponse({"status": "ok"})

    except json.JSONDecodeError as e:
        UserActionLog.objects.create(
            user=None,
            user_name="Bot ManyChat",
            action=f"❌ Error JSON inválido desde ManyChat: {str(e)}",
            page="manychat_log",
            section="errores",
        )
        return JsonResponse({"status": "error"}, status=200)

    except Exception as e:
        UserActionLog.objects.create(
            user=None,
            user_name="Bot ManyChat",
            action=f"❌ Error general en manychat_log: {str(e)}",
            page="manychat_log",
            section="errores",
        )
        return JsonResponse({"status": "error"}, status=200)

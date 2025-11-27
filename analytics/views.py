from datetime import timedelta , date
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q ,Sum
from django.db.models.functions import TruncDate, ExtractHour
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from .models import UserActionLog
from .utils import classify_section
from vendor.models import Profile
from vendor.models import UserPreference, Preference
from django.utils.timezone import now
from django.utils.timezone import localdate

from django.contrib.auth.decorators import login_required




from order.models import Order, OrderItem




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

    # Filtrar por seccion
    if section:
        logs = logs.filter(section__icontains=section)

    logs = logs.order_by("-timestamp")[:400]

    #  CONTADORES
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
    
@staff_member_required
def analytics_data(request):
    """     Devuelve datos para los gráficos de actividad de usuarios.
    Permite filtrar por rango de días 7 o 14.
    """
    try:
        # parametro de rango por defecto 1 semanaa
        rango = int(request.GET.get("rango", 7))
        if rango not in [7, 14]:
            rango = 7  #  fallback en caso de valor invalido
    except ValueError:
        rango = 7

    hoy = now().date()

    #  Generar lista de fechas desde hace 'rango' días hasta hoy
    fecha_inicio = hoy - timedelta(days=rango - 1)
    fechas = [fecha_inicio + timedelta(days=i) for i in range(rango)]

    #  Buscar logs de login o actividad 
    logs = (
        UserActionLog.objects.filter(
            Q(action__icontains="inició sesión")
            | Q(action__icontains="login")
            | Q(action__icontains="visitó")
            | Q(action__icontains="entró"),
            timestamp__date__gte=fecha_inicio,
            timestamp__date__lte=hoy,
        )
        .annotate(fecha=TruncDate("timestamp"))
        .values("fecha")
        .annotate(total=Count("id"))
    )

    # Convertir resultados a diccionario
    data_dict = {str(item["fecha"]): item["total"] for item in logs}

    # Completar los días sin datos con 0
    data_completa = [
        {"fecha": str(f), "total": data_dict.get(str(f), 0)} for f in fechas
    ]

    # Totales generales del sistema
    total = UserActionLog.objects.count()
    errores = UserActionLog.objects.filter(action__icontains="error").count()

    return JsonResponse({
        "usuarios": data_completa,
        "errores": errores,
        "total": total,
        "rango": rango,
    })


@staff_member_required
def graficos(request):
  #  graficos en vivo con chartjs desde mi endpoint  /analytics/api/data/
    return render(request, "analytics/graficos.html")

@staff_member_required
def analytics_horas(request):
    
    periodo = request.GET.get("periodo", "historico")
    hoy = now().date()

    if periodo == "diario":
        logs = UserActionLog.objects.filter(timestamp__date=hoy)
    elif periodo == "semanal":
        logs = UserActionLog.objects.filter(timestamp__date__gte=hoy - timedelta(days=7))
    elif periodo == "mensual":
        logs = UserActionLog.objects.filter(timestamp__date__gte=hoy - timedelta(days=30))
    else:  # histrico
        logs = UserActionLog.objects.all()

    horas = (
        logs.annotate(hora=ExtractHour("timestamp"))
        .values("hora")
        .annotate(total=Count("id"))
        .order_by("hora")
    )

    data = {
        "labels": [f"{h['hora']:02d}:00" for h in horas],
        "values": [h["total"] for h in horas],
    }
    return JsonResponse(data)


def preferences_kpis(request):
    """
    📊 KPI de preferencias alimentarias
    - Usuarios que activaron 'vegano' este mes
    - Ranking de preferencias (add)
    - Total de cambios de preferencias del mes
    """

    today = now()
    month = today.month
    year = today.year

    #  Intentar obtener la preferencia "vegana"
    pref_vegano = Preference.objects.filter(slug="vegana").first()

    # Si existe, contar usuarios veganos este mes
    veganos_mes = 0
    if pref_vegano:
        veganos_mes = UserPreference.objects.filter(
            preference=pref_vegano,
            action="add",
            timestamp__year=year,
            timestamp__month=month,
        ).count()

    # Ranking de preferencias activadas (action="add")
    ranking = list(
        UserPreference.objects.filter(action="add")
        .values("preference__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    # Total cambios del mes (add + remove)
    cambios_mes = UserPreference.objects.filter(
        timestamp__year=year,
        timestamp__month=month,
    ).count()

    return JsonResponse({
        "veganos_mes": veganos_mes,
        "ranking": ranking,
        "cambios_mes": cambios_mes,
    })






# ================================================================
# 📌 FUNCIONES COMUNES
# ================================================================
def get_date_range(range_value):
    today = localdate()

    if range_value == "today":
        return today, today
    if range_value == "7days":
        return today - timedelta(days=7), today
    if range_value == "30days":
        return today - timedelta(days=30), today

    return None, None


# ================================================================
# 📌 VENDOR DASHBOARD: Ventas por día
# ================================================================
@login_required
def vendor_sales_data(request):
    vendor = request.user.vendor
    range_value = request.GET.get("range")

    start_date, end_date = get_date_range(range_value)

    orders = Order.objects.filter(
        vendors=vendor,
        status="paid"               # ← SOLO ÓRDENES PAGADAS
    )

    if start_date:
        orders = orders.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

    data = (
        orders.annotate(day=TruncDate("created_at"))
              .values("day")
              .annotate(total=Count("id"))
              .order_by("day")
    )

    return JsonResponse(
        [{"day": str(d["day"]), "total": d["total"]} for d in data],
        safe=False
    )


# ================================================================
# 📌 VENDOR DASHBOARD: Productos más vendidos
# ================================================================
@login_required
def vendor_top_products(request):
    vendor = request.user.vendor
    range_value = request.GET.get("range")

    start_date, end_date = get_date_range(range_value)

    items = OrderItem.objects.filter(
        vendor=vendor,
        order__status="paid"        # ← SOLO items de órdenes pagadas
    )

    if start_date:
        items = items.filter(
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date
        )

    data = (
        items.values("product__title")
             .annotate(total=Sum("quantity"))
             .order_by("-total")
    )

    return JsonResponse(
        [{"product": d["product__title"], "total": d["total"]} for d in data],
        safe=False
    )


# ================================================================
# 📌 ADMIN DASHBOARD: Ventas por día (GLOBAL)
# ================================================================
@staff_member_required
def admin_sales_data(request):
    rango = request.GET.get("range", "7days")
    start, end = get_date_range(rango)

    orders = Order.objects.filter(status="paid")  # ← SOLO pagadas

    if start:
        orders = orders.filter(
            created_at__date__gte=start,
            created_at__date__lte=end
        )

    data = (
        orders.annotate(day=TruncDate("created_at"))
              .values("day")
              .annotate(total=Count("id"))
              .order_by("day")
    )

    return JsonResponse(
        [{"day": d["day"].strftime("%Y-%m-%d"), "total": d["total"]} for d in data],
        safe=False
    )


# ================================================================
# 📌 ADMIN DASHBOARD: Productos más vendidos (GLOBAL)
# ================================================================
@staff_member_required
def admin_top_products(request):
    rango = request.GET.get("range", "7days")
    start, end = get_date_range(rango)

    items = OrderItem.objects.filter(order__status="paid")  # ← SOLO pagadas

    if start:
        items = items.filter(
            order__created_at__date__gte=start,
            order__created_at__date__lte=end
        )

    data = (
        items.values("product__title")
             .annotate(total=Sum("quantity"))
             .order_by("-total")
    )

    return JsonResponse(
        [{"product": d["product__title"], "total": d["total"]} for d in data],
        safe=False
    )
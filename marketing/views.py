from django.http import JsonResponse
from django.contrib.auth.models import User

# def users_list(request):
#     users = User.objects.all().select_related("profile")

#     data = []

#     for user in users:
#         profile = getattr(user, "profile", None)

#         if not profile:
#             continue  # si algún usuario no tiene perfil, se salta

#         data.append({
#             "id": user.id,
#             "email": user.email,
#             "name": user.username,
#             "phone": str(profile.phone) if profile.phone else None,
#             "country": profile.country.iso_code if profile.country else None,
#             "preferences": list(profile.preferences.values_list("slug", flat=True)),
#         })

#     return JsonResponse({"users": data})





def email_list(request):
    """
    Devuelve un listado limpio de usuarios para campañas:
    - Solo usuarios activos
    - Solo usuarios con email NO vacío
    """
    users_qs = (
        User.objects
        .filter(is_active=True)
        .exclude(email__isnull=True)
        .exclude(email__exact="")
        .order_by("id")
    )

    data = []

    for user in users_qs:
        data.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,          # 👈 clave estándar
            "first_name": user.first_name,
            "last_name": user.last_name,
            # si quieres agregar más campos, los pones aquí
        })

    return JsonResponse(
        {
            "count": len(data),
            "users": data,
        }
    )



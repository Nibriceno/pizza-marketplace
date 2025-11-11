import traceback
from django.utils.deprecation import MiddlewareMixin
from .models import UserActionLog


class ErrorLoggingMiddleware(MiddlewareMixin):
    """
    Captura y registra automáticamente errores no controlados en todo el proyecto.
    Guarda usuario, error y ruta donde ocurrió.
    """

    def process_exception(self, request, exception):
        try:
            # 🚫 Evitar registrar errores que provienen del propio sistema de analytics
            # (por ejemplo, /analytics/manychat, /analytics/dashboard, /analytics/error)
            if request.path.startswith("/analytics/"):
                return None

            # Obtener usuario autenticado (si lo hay)
            user = (
                request.user
                if hasattr(request, "user") and request.user.is_authenticated
                else None
            )

            # Mensaje de error principal
            error_message = f"❌ ERROR GLOBAL: {type(exception).__name__} - {str(exception)}"

            # Registrar log en base de datos
            UserActionLog.objects.create(
                user=user,
                user_name=getattr(user, "username", "Anónimo") if user else "Sistema",
                action=error_message,
                page=request.path,
            )

            # Mostrar traceback completo en consola (solo en desarrollo)
            print("⚠️ Error capturado por middleware:")
            print(traceback.format_exc())

        except Exception as e:
            # Si ocurre un error al intentar registrar el log, lo mostramos por consola
            print(f"⚠️ No se pudo registrar el error global: {e}")
            print(traceback.format_exc())
            pass

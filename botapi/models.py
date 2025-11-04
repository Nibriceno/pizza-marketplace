from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from product.models import Product


# 🛒 Carrito temporal (usado por el bot ManyChat)
class TempCart(models.Model):
    """
    Carrito temporal usado por el bot de ManyChat antes de que el usuario inicie sesión.
    """
    token = models.CharField(max_length=100, unique=True, verbose_name="Token del carrito")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")

    class Meta:
        verbose_name = "Carrito Temporal"
        verbose_name_plural = "Carritos Temporales"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Carrito #{self.token[:8]}"

    def total(self):
        """Suma total de los productos del carrito."""
        return sum(item.subtotal() for item in self.items.all())

    def cantidad_total(self):
        """Cantidad total de productos en el carrito."""
        return sum(item.quantity for item in self.items.all())


# 🧾 Items dentro del carrito temporal
class TempItem(models.Model):
    """
    Item dentro de un carrito temporal (producto + cantidad).
    """
    cart = models.ForeignKey(TempCart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name="Cantidad")

    class Meta:
        verbose_name = "Item Temporal"
        verbose_name_plural = "Items Temporales"

    def __str__(self):
        return f"{self.product.title} × {self.quantity}"

    def subtotal(self):
        """Subtotal del ítem (precio × cantidad)."""
        return self.product.price * self.quantity


# 🔐 Token temporal de login automático
class LoginToken(models.Model):
    """
    Token de login temporal para acceder automáticamente al carrito sin ingresar credenciales.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        """Verifica si el token sigue siendo válido (no expirado)."""
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Token de {self.user.username} (expira {self.expires_at:%H:%M:%S})"

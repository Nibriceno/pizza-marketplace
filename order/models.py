from django.db import models
from product.models import Product
from vendor.models import Vendor


class Order(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_amount = models.IntegerField(default=0)

    # 🔹 NUEVOS CAMPOS
    paid = models.BooleanField(default=False)  # ✅ permite marcar la orden como pagada
    status = models.CharField(                 # opcional, para mostrar el estado del pedido
        max_length=20,
        choices=[
            ("pending", "Pendiente"),
            ("paid", "Pagada"),
            ("cancelled", "Cancelada"),
        ],
        default="pending",
    )

    vendors = models.ManyToManyField(Vendor, related_name="orders")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Orden #{self.id} - {self.first_name} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="items", on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, related_name="items", on_delete=models.CASCADE)
    vendor_paid = models.BooleanField(default=False)
    price = models.IntegerField()
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"Item #{self.id} ({self.product.title})"

    def get_total_price(self):
        return self.price * self.quantity

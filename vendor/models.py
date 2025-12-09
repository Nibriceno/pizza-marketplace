from django.contrib.auth.models import User
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from core.models import Country
from location.models import Region, Provincia, Comuna
from django.utils.text import slugify 



class Preference(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Preferencia"
        verbose_name_plural = "Preferencias"
        ordering = ['name']


class Allergy(models.Model):
    """
    Alergia alimentaria general (Gluten, Lactosa, Frutos secos, etc.)
    Se asocia a ingredientes concretos (product.Ingredient) y a usuarios vía Profile.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    # Ingredientes que gatillan esta alergia
    ingredients = models.ManyToManyField(
        "product.Ingredient",          # 👈 referencia perezosa para evitar import circular
        related_name="allergies",
        blank=True,
        verbose_name="Ingredientes relacionados",
    )

    class Meta:
        verbose_name = "Alergia"
        verbose_name_plural = "Alergias"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Genera un slug único basado en el name si no existe."""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            num = 1

            while Allergy.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1

            self.slug = slug

        super().save(*args, **kwargs)


class Vendor(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.OneToOneField(User, related_name='vendor', on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_balance(self):
        items = self.items.filter(vendor_paid=False, order__vendors__in=[self.id])
        return sum((item.product.price * item.quantity) for item in items)

    def get_paid_amount(self):
        items = self.items.filter(vendor_paid=True, order__vendors__in=[self.id])
        return sum((item.product.price * item.quantity) for item in items)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # País y localizacion
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    provincia = models.ForeignKey(Provincia, on_delete=models.SET_NULL, null=True, blank=True)
    comuna = models.ForeignKey(Comuna, on_delete=models.SET_NULL, null=True, blank=True)

    # Información de contacto
    phone = PhoneNumberField(region='CL', blank=True)
    address = models.CharField(max_length=255)
    zipcode = models.CharField(max_length=255)

    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Preferencias alimentarias (vegano / sin gluten / más a futuro)
    preferences = models.ManyToManyField(Preference, blank=True)

    # Alergias alimentarias del usuario
    allergies = models.ManyToManyField(
        Allergy,
        blank=True,
        related_name="profiles",
        verbose_name="Alergias alimentarias",
    )

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"
        ordering = ['user__username']


class UserPreference(models.Model):
    ACTIONS = (
        ('add', 'add'),
        ('remove', 'remove'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    preference = models.ForeignKey(Preference, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Preferencia del Usuario"
        verbose_name_plural = "Preferencias del Usuario"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.preference.name} - {self.action}"





class VendorWeeklyMenu(models.Model):
    vendor = models.ForeignKey(
        "vendor.Vendor", on_delete=models.CASCADE, related_name="weekly_menus"
    )
    date = models.DateField()  # Día específico (lunes a domingo)
    product = models.ForeignKey(
        "product.Product", on_delete=models.CASCADE, related_name="weekly_menus"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("vendor", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.vendor} - {self.date} - {self.product}"
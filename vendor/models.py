from django.contrib.auth.models import User
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from core.models import Country
from location.models import Region, Provincia, Comuna



class Preference(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Preferencia"
        verbose_name_plural = "Preferencias"
        ordering = ['name']


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


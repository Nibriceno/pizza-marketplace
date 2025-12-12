from django import forms
from vendor.models import VendorWeeklyMenu, Vendor
from product.models import Product
from offers.models import Offer
from django.db.models import Max 
from product.models import Product, Ingredient, IngredientCategory
class VendorWeeklyMenuForm(forms.ModelForm):
    class Meta:
        model = VendorWeeklyMenu
        fields = ["vendor", "date", "product"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Sólo por orden, no es obligatorio
        self.fields["vendor"].queryset = Vendor.objects.order_by("name")
        self.fields["product"].queryset = Product.objects.order_by("vendor__name", "title")







class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = [
            "product",
            "discount_percentage",
            "discount_price",
            "is_2x1",
            "start_date",
            "end_date",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ordenar productos por vendor y nombre
        self.fields["product"].queryset = Product.objects.select_related("vendor").order_by(
            "vendor__name", "title"
        )


# superadmin_panel/forms.py
from django import forms
from django.contrib.auth import get_user_model
from vendor.models import Vendor

User = get_user_model()


from django import forms
from django.contrib.auth.models import User

from vendor.models import Vendor, Profile
from vendor.geocoding import geocode_address  # si lo creaste, si no, lo comentas

class VendorEditForm(forms.ModelForm):
    # ====== USER ======
    username = forms.CharField(label="Usuario", max_length=150)
    email = forms.EmailField(label="Correo electrónico", required=False)

    new_password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput, required=False)
    new_password2 = forms.CharField(label="Repetir nueva contraseña", widget=forms.PasswordInput, required=False)

    # ====== PROFILE (local) ======
    country = forms.ModelChoiceField(queryset=None, required=False, label="País")
    region = forms.ModelChoiceField(queryset=None, required=False, label="Región")
    provincia = forms.ModelChoiceField(queryset=None, required=False, label="Provincia")
    comuna = forms.ModelChoiceField(queryset=None, required=False, label="Comuna")

    phone = forms.CharField(label="Teléfono", required=False)
    address = forms.CharField(label="Dirección", required=False)
    zipcode = forms.CharField(label="Código postal", required=False)

    class Meta:
        model = Vendor
        fields = []  # ✅ no usamos campos de Vendor porque tu Vendor no tiene "name"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        vendor = self.instance
        user = vendor.created_by

        # ====== USER initial ======
        self.fields["username"].initial = user.username
        self.fields["email"].initial = user.email

        # ====== PROFILE instance ======
        profile = getattr(user, "profile", None)
        if profile is None:
            profile = Profile(user=user)

        # Import aquí para evitar problemas de import circular
        from core.models import Country
        from location.models import Region, Provincia, Comuna

        self.fields["country"].queryset = Country.objects.all().order_by("name")
        self.fields["region"].queryset = Region.objects.all().order_by("name")

        # dependientes
        if profile.region_id:
            self.fields["provincia"].queryset = Provincia.objects.filter(region_id=profile.region_id).order_by("name")
        else:
            self.fields["provincia"].queryset = Provincia.objects.none()

        if profile.provincia_id:
            self.fields["comuna"].queryset = Comuna.objects.filter(provincia_id=profile.provincia_id).order_by("name")
        else:
            self.fields["comuna"].queryset = Comuna.objects.none()

        # ====== PROFILE initial ======
        self.fields["country"].initial = profile.country_id
        self.fields["region"].initial = profile.region_id
        self.fields["provincia"].initial = profile.provincia_id
        self.fields["comuna"].initial = profile.comuna_id

        self.fields["phone"].initial = str(profile.phone) if getattr(profile, "phone", None) else ""
        self.fields["address"].initial = profile.address or ""
        self.fields["zipcode"].initial = profile.zipcode or ""

    def clean_username(self):
        username = self.cleaned_data["username"]
        qs = User.objects.exclude(pk=self.instance.created_by_id).filter(username=username)
        if qs.exists():
            raise forms.ValidationError("Ya existe un usuario con este nombre de usuario.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")

        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Las contraseñas no coinciden.")
            if len(p1) < 6:
                raise forms.ValidationError("La contraseña debe tener al menos 6 caracteres.")
        return cleaned

    def save(self, commit=True):
        vendor = super().save(commit=False)  # aunque no tenga fields, no pasa nada
        user = vendor.created_by

        # ====== USER ======
        user.username = self.cleaned_data["username"]
        user.email = (self.cleaned_data.get("email") or "").strip()

        new_password = self.cleaned_data.get("new_password1")
        if new_password:
            user.set_password(new_password)

        # ====== PROFILE ======
        profile = getattr(user, "profile", None)
        if profile is None:
            profile = Profile(user=user)

        profile.country = self.cleaned_data.get("country")
        profile.region = self.cleaned_data.get("region")
        profile.provincia = self.cleaned_data.get("provincia")
        profile.comuna = self.cleaned_data.get("comuna")

        profile.phone = self.cleaned_data.get("phone") or ""
        profile.address = self.cleaned_data.get("address") or ""
        profile.zipcode = self.cleaned_data.get("zipcode") or ""

        # ====== geocoding ======
        try:
            comuna_obj = profile.comuna
            region_obj = profile.region
            country_obj = profile.country

            comuna_name = getattr(comuna_obj, "name", str(comuna_obj) if comuna_obj else "")
            region_name = getattr(region_obj, "name", str(region_obj) if region_obj else "")
            country_name = getattr(country_obj, "name", "Chile")

            if profile.address and comuna_name:
                lat, lng = geocode_address(
                    address=profile.address,
                    comuna=comuna_name,
                    region=region_name,
                    country=country_name,
                )
                profile.lat = lat
                profile.lng = lng
        except Exception:
            pass

        if commit:
            user.save()
            vendor.save()   # guarda si cambiaste algo en Vendor (aunque no haya fields)
            profile.save()
        else:
            self._user_to_save = user
            self._profile_to_save = profile

        return vendor



class IngredientCategoryForm(forms.ModelForm):
    # hacemos explícito el campo ordering
    ordering = forms.IntegerField(
        label="Posición en la lista",
        min_value=1,
        required=False,
        help_text="1 = aparece primero. Si lo dejas vacío, se pondrá al final.",
        widget=forms.NumberInput(attrs={
            "class": "input",
            "placeholder": "Ej: 1 para arriba, 10 para más abajo",
        }),
    )

    class Meta:
        model = IngredientCategory
        fields = ["name", "ordering"]
        labels = {
            "name": "Nombre de la categoría",
        }
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "Ej: Carnes, Quesos, Salsas…",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si es una categoría nueva y no viene ordering, sugerimos el último + 1
        if not self.instance.pk and not self.initial.get("ordering"):
            max_order = IngredientCategory.objects.aggregate(
                m=Max("ordering")
            )["m"] or 0
            self.fields["ordering"].initial = max_order + 1

    def clean_ordering(self):
        value = self.cleaned_data.get("ordering")

        # Si el admin no escribe nada, ponemos último + 1
        if value in (None, ""):
            max_order = IngredientCategory.objects.aggregate(
                m=Max("ordering")
            )["m"] or 0
            return max_order + 1

        return value


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ["category", "name"]
        labels = {
            "category": "Categoría",
            "name": "Nombre del ingrediente",
        }
        widgets = {
            "category": forms.Select(attrs={"class": "select"}),
            "name": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "Ej: Queso mozzarella, Pepperoni…",
            }),
        }


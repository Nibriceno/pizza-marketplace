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


class VendorEditForm(forms.ModelForm):
    username = forms.CharField(label="Usuario", max_length=150)
    email = forms.EmailField(label="Correo electrónico", required=False)
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput,
        required=False,
    )
    new_password2 = forms.CharField(
        label="Repetir nueva contraseña",
        widget=forms.PasswordInput,
        required=False,
    )

    class Meta:
        model = Vendor
        fields = ["name", "country"]  # ajusta según tu modelo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance.created_by
        self.fields["username"].initial = user.username
        self.fields["email"].initial = user.email

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
        vendor = super().save(commit=False)
        user = vendor.created_by

        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data.get("email", "")

        new_password = self.cleaned_data.get("new_password1")
        if new_password:
            user.set_password(new_password)

        if commit:
            user.save()
            vendor.save()
        else:
            # si decides usar commit=False en algún momento
            self._user_to_save = user

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


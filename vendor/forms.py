from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import re
from phonenumber_field.formfields import PhoneNumberField
from core.models import Country
from .models import Profile
from product.models import Product
from django.forms import ModelForm


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'image', 'title', 'description', 'price']


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=255, required=True)
    last_name  = forms.CharField(max_length=255, required=True)
    email      = forms.EmailField(max_length=255, required=True)

    # Declaramos el campo con queryset vacío; lo llenamos en __init__
    country = forms.ModelChoiceField(
        queryset=Country.objects.none(),
        empty_label='Selecciona un país',
        required=True,
        widget=forms.Select()
    )

    phone = PhoneNumberField(
        region='CL',
        required=True,
        error_messages={
            'invalid': 'Por favor ingresa un número válido con el código de país.'
        },
        widget=forms.TextInput(attrs={'placeholder': 'Selecciona país primero'})
    )

    address = forms.CharField(max_length=255, required=True)
    zipcode = forms.CharField(max_length=255, required=True)
    place   = forms.CharField(max_length=255, required=True)

    class Meta:
        model  = User
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'country', 'phone', 'address', 'zipcode', 'place',
            'password1', 'password2',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Cargamos países aquí para evitar problemas de import/registro de apps
        self.fields['country'].queryset = Country.objects.all().order_by('name')

        # Clases Bulma para inputs
        input_like = [
            'username','first_name','last_name','email',
            'phone','address','zipcode','place',
            'password1','password2'
        ]
        for name in input_like:
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault('class', 'input')

        # Placeholders
        placeholders = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'phone': '+56 9 1234 5678',
            'address': 'Dirección',
            'zipcode': 'Código postal',
            'place': 'Ciudad o localidad',
            'password1': 'Contraseña',
            'password2': 'Confirmar contraseña'
        }
        for name, ph in placeholders.items():
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault('placeholder', ph)

    def clean_country(self):
        country = self.cleaned_data.get('country')
        if not country:
            raise forms.ValidationError("Debes seleccionar un país.")
        return country

    import re

    def clean_phone(self):
        """
        ✅ Valida y normaliza el número de teléfono según el país seleccionado.
        - Debe comenzar con el código de país (ej: +56).
        - Si el país tiene prefijo móvil, debe ir inmediatamente después (ej: 9 en Chile).
        - Se limpian espacios y guiones para dejarlo en formato internacional limpio.
        """
        phone = self.cleaned_data.get('phone')
        country = self.cleaned_data.get('country')

        # Convertimos a string si viene como objeto PhoneNumber
        phone_str = str(phone) if phone is not None else ''
        if not country:
            raise forms.ValidationError("Debes seleccionar un país.")

        # Limpiar espacios, guiones y caracteres no numéricos (excepto el '+')
        phone_str = re.sub(r'[^0-9+]', '', phone_str)

        code = country.phone_code.strip()              # Ej: "+56"
        prefix = (country.mobile_prefix or '').strip() # Ej: "9" o ""

        # Validar código de país
        if not phone_str.startswith(code):
            raise forms.ValidationError(
                f"El número debe comenzar con {code} para {country.name}."
            )

        # Cortar lo que viene después del código de país
        after_code = phone_str[len(code):]

        # Validar prefijo móvil si existe
        if prefix and not after_code.startswith(prefix):
            raise forms.ValidationError(
                f"En {country.name} los móviles deben comenzar con {prefix} después de {code}."
            )

        # ✅ Normalizamos el número final — sin espacios ni guiones
        normalized_number = code + after_code

        # Reasignar el número normalizado en los datos limpios
        self.cleaned_data['phone'] = normalized_number
        return normalized_number


    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']

        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                country=self.cleaned_data['country'],
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                zipcode=self.cleaned_data['zipcode'],
                place=self.cleaned_data['place']
            )
        return user

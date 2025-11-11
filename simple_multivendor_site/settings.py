import os
from pathlib import Path
from dotenv import load_dotenv

# 📌 Cargar variables de entorno
load_dotenv()

# 📁 BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# 🛡️ Seguridad
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')

# ⚠️ Importante: pon DEBUG en False en producción real
DEBUG =True

# 🌐 Hosts permitidos — incluye tu dominio de PythonAnywhere
ALLOWED_HOSTS = [
    'nicolasbriceno.pythonanywhere.com',
    '127.0.0.1',
    'localhost',
    'nonfimbriate-usha-aerobically.ngrok-free.dev'
]

CSRF_TRUSTED_ORIGINS = [
    "https://nonfimbriate-usha-aerobically.ngrok-free.dev",
    "https://nicolasbriceno.pythonanywhere.com"
]

# 📦 Apps instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'vendor',
    'product',
    'cart',
    'order',
    'widget_tweaks',
    'location',
    'botapi',
     # 🔸 app de logs
    'analytics',  # 👈 agrégala aquí
    
]

# 🧱 Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # 🧱 Middleware personalizado de logs
    'analytics.middleware.ErrorLoggingMiddleware',
]

# 🌍 URL y Templates
ROOT_URLCONF = 'simple_multivendor_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Directorio global para templates
        'APP_DIRS': True,  # Asegura que Django busque también en las carpetas de cada app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'product.context_processors.menu_categories',
                'cart.context_processors.cart',
            ],
        },
    },
]



WSGI_APPLICATION = 'simple_multivendor_site.wsgi.application'

# 🧭 Base de datos (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 🔐 Password validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 🌍 Internacionalización
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# 📁 Archivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'core/static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 🖼️ Archivos media
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 🧑‍💻 Login & sesiones
LOGIN_URL = 'vendor:login'
LOGIN_REDIRECT_URL = 'vendor:vendor-admin'
LOGOUT_REDIRECT_URL = 'core:home'

SESSION_COOKIE_AGE = 86400  # 1 día en segundos
CART_SESSION_ID = 'cart'

# settings.py
MERCADOPAGO_SANDBOX = True  # Cambia a False cuando vayas a producción

# 💳 Stripe (desde .env)
STRIPE_PUB_KEY = 'pk_test_OKdhbDNME5KHtnpzYRBfNmEZ00mjM6DVsJ'  # publica
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

# 📧 Email (ajústalo si usarás notificaciones)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "nicolas.bricenocq@gmail.com"
EMAIL_HOST_PASSWORD = "kqqqfatfoabsxasd"  # tu nueva contraseña de aplicación, sin espacios
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# 💳 Mercado Pago
MERCADOPAGO_PUBLIC_KEY = os.getenv('MERCADOPAGO_PUBLIC_KEY', '')
MERCADOPAGO_ACCESS_TOKEN = os.getenv('MERCADOPAGO_ACCESS_TOKEN', '')
MERCADOPAGO_WEBHOOK_SECRET =os.getenv('MERCADOPAGO_WEBHOOK_SECRET', '')


MANYCHAT_SECRET = "fh+##3lsl221#@$%$%^%$@"

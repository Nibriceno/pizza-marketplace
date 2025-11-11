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
DEBUG = True

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
    'analytics',  # 👈 app de logs
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
    'analytics.middleware.ErrorLoggingMiddleware',  # 🧱 Middleware personalizado de logs
]

# 🌍 URL y Templates
ROOT_URLCONF = 'simple_multivendor_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
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

# Configuración dinámica de URLs
BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:8000')  # Usará BASE_URL de .env
PROD_BASE_URL = os.getenv('PROD_BASE_URL', 'https://tusitio.pythonanywhere.com')  # Para producción

# Determinar si estamos en ngrok o en local
if 'ngrok' in os.getenv('BASE_URL', ''):
    BASE_URL = os.getenv('NGROK_BASE_URL', 'https://nonfimbriate-usha-aerobically.ngrok-free.dev')

# 💳 Mercado Pago
MERCADOPAGO_PUBLIC_KEY = os.getenv('MERCADOPAGO_PUBLIC_KEY', '')
MERCADOPAGO_ACCESS_TOKEN = os.getenv('MERCADOPAGO_ACCESS_TOKEN', '')
MERCADOPAGO_WEBHOOK_SECRET = os.getenv('MERCADOPAGO_WEBHOOK_SECRET', '')

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

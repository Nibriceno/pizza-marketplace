from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🏠 Página principal: core (frontpage)
    path('', include('core.urls')),

    # 🧭 Rutas específicas: ponlas antes de product
    path('vendor/', include('vendor.urls')),
    path('cart/', include('cart.urls')),
    path('order/', include('order.urls')),

    # 🍕 Productos
    path('product/', include('product.urls')),

    # 🚪 Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

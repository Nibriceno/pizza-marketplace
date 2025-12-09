from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import profile_view, select_preferences, edit_preferences


app_name = 'vendor'


urlpatterns = [
    # Página de listado de vendedores
    path('', views.vendors, name="vendors"),

    # Registro
    path('become-vendor/', views.register_vendor_view, name="become-vendor"),
    path('become-customer/', views.register_customer_view, name="become-customer"),

    # Panel del vendedor antiguo
    path('vendor-admin/', views.vendor_admin, name="vendor-admin"),
    path('edit-vendor/', views.edit_vendor, name="edit-vendor"),

    # Productos
    path('add-product/', views.add_product, name="add-product"),
    path('delete-product/<int:pk>/', views.delete_product, name="delete-product"),
    path("product/<int:product_id>/offer/", views.edit_offer, name="edit-offer"),

    # Perfil / preferencias
    path("profile/", profile_view, name="profile"),
    path("select-preferences/", select_preferences, name="select-preferences"),
    path("edit-preferences/", edit_preferences, name="edit-preferences"),

    # Página del vendedor individual (vitrina pública)
    path('<int:vendor_id>/', views.vendor, name="vendor"),

    # 🚀 DASHBOARD NUEVO DEL VENDEDOR
    path("dashboard/", views.vendor_dashboard, name="vendor_dashboard"),




    path("weekly-menu/", views.weekly_menu_edit, name="weekly_menu_edit"),
    path("weekly-menu/assign/", views.weekly_menu_assign, name="weekly_menu_assign"),
    path("weekly-menu/history/", views.weekly_menu_history, name="weekly_menu_history"),
     path("weekly-menu/clear/", views.weekly_menu_clear, name="weekly_menu_clear"),
]

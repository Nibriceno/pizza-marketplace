
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import profile_view, select_preferences, edit_preferences


app_name = 'vendor'


urlpatterns = [
    path('', views.vendors, name="vendors"),
    path('become-vendor/', views.register_vendor_view, name="become-vendor"),
    path('become-customer/', views.register_customer_view, name="become-customer"),

    path('vendor-admin/', views.vendor_admin, name="vendor-admin"),
    path('edit-vendor/', views.edit_vendor, name="edit-vendor"),

    path('add-product/', views.add_product, name="add-product"),
    path('delete-product/<int:pk>/', views.delete_product, name="delete-product"),

  #  path('logout/', auth_views.LogoutView.as_view(), name="logout"),
    # path('login/', auth_views.LoginView.as_view(template_name='vendor/login.html'), name="login"),
    path('<int:vendor_id>/', views.vendor, name="vendor"),

    path("profile/", profile_view, name="profile"),
    path("select-preferences/", select_preferences, name="select-preferences"),
    path("edit-preferences/", edit_preferences, name="edit-preferences"),
    
]

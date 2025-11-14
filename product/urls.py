from django.urls import path
from . import views

app_name = 'product'

urlpatterns = [
    path('', views.home, name='home'), 
    path('search', views.search, name="search"),
    path('<slug:category_slug>/<slug:product_slug>/', views.product, name="product"),
    path('<slug:category_slug>/', views.category, name="category"),

]

from django.urls import path
from . import views

app_name = 'analytics' 

urlpatterns = [
    path('dashboard/', views.dashboard, name='analytics_dashboard'),
    path('manychat/', views.manychat_log, name='analytics_manychat'),
    path('graficos/', views.graficos, name='graficos'),
    path('api/data/', views.analytics_data, name='analytics_data'),
    path("api/horas/", views.analytics_horas, name="analytics_horas"),
    



]

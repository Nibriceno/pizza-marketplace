from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='analytics_dashboard'),
    path('manychat/', views.manychat_log, name='analytics_manychat'),
    
]

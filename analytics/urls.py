from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='analytics_dashboard'),
    path('manychat/', views.manychat_log, name='analytics_manychat'),
    path('manychat-error/', views.manychat_error_log, name='manychat_error_log'),
]

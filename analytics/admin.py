from django.contrib import admin
from .models import UserActionLog

@admin.register(UserActionLog)
class UserActionLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'page', 'product_id')
    list_filter = ('action', 'page', 'created_at')
    search_fields = ('user__username', 'action', 'page')

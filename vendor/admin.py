from django.contrib import admin
from .models import Vendor

from .models import Profile


admin.site.register(Vendor)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'country', 
        'region', 
        'provincia', 
        'comuna', 
        'phone', 
        'address', 
        'zipcode', 
        'created_at'
    )
    list_filter = ('country', 'region', 'provincia', 'comuna')
    search_fields = ('user__username', 'user__email', 'phone', 'address')
    ordering = ('user__username',)
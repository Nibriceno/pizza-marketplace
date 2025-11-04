from django.contrib import admin
from .models import TempCart, TempItem

class TempItemInline(admin.TabularInline):
    model = TempItem
    extra = 0
    readonly_fields = ("product", "quantity", "subtotal_display")

    def subtotal_display(self, obj):
        return f"${obj.subtotal():,.0f}"
    subtotal_display.short_description = "Subtotal"

@admin.register(TempCart)
class TempCartAdmin(admin.ModelAdmin):
    list_display = ("token", "created_at", "total_display", "cantidad_total")
    inlines = [TempItemInline]
    readonly_fields = ("token", "created_at")

    def total_display(self, obj):
        return f"${obj.total():,.0f}"
    total_display.short_description = "Total"

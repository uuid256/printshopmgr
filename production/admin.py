from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Material, MaterialUsage, ProductType


@admin.register(ProductType)
class ProductTypeAdmin(ModelAdmin):
    list_display = ("name", "pricing_method", "base_price", "unit", "requires_design", "is_active", "sort_order")
    list_filter = ("pricing_method", "requires_design", "is_active")
    list_editable = ("sort_order", "is_active")
    search_fields = ("name", "name_en")


@admin.register(Material)
class MaterialAdmin(ModelAdmin):
    list_display = ("name", "quantity_in_stock", "unit", "cost_per_unit", "min_quantity", "is_low_stock", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)

    @admin.display(boolean=True, description="สต็อกต่ำ")
    def is_low_stock(self, obj):
        return obj.is_low_stock


@admin.register(MaterialUsage)
class MaterialUsageAdmin(ModelAdmin):
    list_display = ("material", "quantity_used", "recorded_at")
    list_filter = ("material",)
    readonly_fields = ("recorded_at",)

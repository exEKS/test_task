from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("full_title", "parser_type", "regular_price", "sale_price", "parsed_at")
    list_filter = ("parser_type",)
    search_fields = ("full_title", "product_code", "manufacturer")
    readonly_fields = ("parsed_at",)

from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_count', 'created_at']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price', 'quantity', 'stock_status_display', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'sku', 'description']
    list_editable = ['price', 'quantity', 'is_active']

from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'product_count', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'sku', 'name', 'category', 'season', 'gender',
        'color', 'size', 'price', 'quantity', 'stock_status_display', 'is_active'
    ]
    list_filter = ['category', 'season', 'gender', 'color', 'size', 'is_active']
    search_fields = ['name', 'sku', 'description']
    list_editable = ['price', 'quantity', 'is_active']
    readonly_fields = ['sku', 'created_at', 'updated_at']

    fieldsets = (
        ('Product Info', {
            'fields': ('name', 'sku', 'category', 'description', 'image')
        }),
        ('Clothing Attributes (Used for SKU)', {
            'fields': ('season', 'gender', 'color', 'size'),
            'description': 'These fields determine the auto-generated SKU'
        }),
        ('Pricing', {
            'fields': ('price', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('quantity', 'low_stock_threshold', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make SKU readonly only when editing existing product."""
        if obj:  # Editing existing object
            return self.readonly_fields
        # For new objects, SKU is not shown (auto-generated on save)
        return ['created_at', 'updated_at']

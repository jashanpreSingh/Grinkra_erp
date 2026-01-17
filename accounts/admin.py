from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'phone', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'can_add_product', 'can_create_invoice', 'can_manage_users']
    search_fields = ['username', 'email', 'phone']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Contact', {
            'fields': ('role', 'phone')
        }),
        ('Inventory Permissions', {
            'fields': (
                'can_view_inventory',
                'can_add_product',
                'can_edit_product', 
                'can_delete_product',
                'can_manage_categories',
                'can_adjust_stock',
            ),
            'classes': ('collapse',),
        }),
        ('Billing Permissions', {
            'fields': (
                'can_view_billing',
                'can_create_invoice',
                'can_cancel_invoice',
                'can_manage_customers',
            ),
            'classes': ('collapse',),
        }),
        ('User Management', {
            'fields': ('can_manage_users',),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Contact', {
            'fields': ('role', 'phone')
        }),
        ('Inventory Permissions', {
            'fields': (
                'can_view_inventory',
                'can_add_product',
                'can_edit_product',
                'can_delete_product',
                'can_manage_categories',
                'can_adjust_stock',
            ),
        }),
        ('Billing Permissions', {
            'fields': (
                'can_view_billing',
                'can_create_invoice',
                'can_cancel_invoice',
                'can_manage_customers',
            ),
        }),
        ('User Management', {
            'fields': ('can_manage_users',),
        }),
    )

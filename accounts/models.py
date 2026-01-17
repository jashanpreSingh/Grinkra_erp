from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Inventory Permissions
    can_view_inventory = models.BooleanField(default=True, verbose_name="Can View Inventory")
    can_add_product = models.BooleanField(default=False, verbose_name="Can Add Product")
    can_edit_product = models.BooleanField(default=False, verbose_name="Can Edit Product")
    can_delete_product = models.BooleanField(default=False, verbose_name="Can Delete Product")
    can_manage_categories = models.BooleanField(default=False, verbose_name="Can Manage Categories")
    can_adjust_stock = models.BooleanField(default=False, verbose_name="Can Adjust Stock")

    # Billing Permissions
    can_view_billing = models.BooleanField(default=True, verbose_name="Can View Billing")
    can_create_invoice = models.BooleanField(default=True, verbose_name="Can Create Invoice")
    can_cancel_invoice = models.BooleanField(default=False, verbose_name="Can Cancel Invoice")
    can_manage_customers = models.BooleanField(default=True, verbose_name="Can Manage Customers")

    # User Management Permissions
    can_manage_users = models.BooleanField(default=False, verbose_name="Can Manage Users")

    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

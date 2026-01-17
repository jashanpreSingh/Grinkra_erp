from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import CustomUser
from .forms import CustomAuthenticationForm, CustomUserCreationForm, CustomUserUpdateForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return login_required(wrapper)


@admin_required
def user_list(request):
    users = CustomUser.objects.all().order_by('-created_at')
    return render(request, 'accounts/user_list.html', {'users': users})


@admin_required
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            return redirect('user_list')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Create User'})


@admin_required
def user_edit(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)

    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('user_list')
    else:
        form = CustomUserUpdateForm(instance=user)

    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Edit User'})


@admin_required
@require_POST
def user_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot delete yourself.')
    else:
        user.delete()
        messages.success(request, 'User deleted successfully.')
    return redirect('user_list')


@admin_required
def user_permissions(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)

    # Define all permission fields
    inventory_permissions = [
        ('can_view_inventory', 'View Inventory', 'View products and categories'),
        ('can_add_product', 'Add Product', 'Create new products'),
        ('can_edit_product', 'Edit Product', 'Edit existing products'),
        ('can_delete_product', 'Delete Product', 'Delete products'),
        ('can_manage_categories', 'Manage Categories', 'Add, edit, delete categories'),
        ('can_adjust_stock', 'Adjust Stock', 'Adjust product stock levels'),
    ]

    billing_permissions = [
        ('can_view_billing', 'View Billing', 'View invoices and customers'),
        ('can_create_invoice', 'Create Invoice', 'Create new invoices'),
        ('can_cancel_invoice', 'Cancel Invoice', 'Cancel existing invoices'),
        ('can_manage_customers', 'Manage Customers', 'Add, edit, delete customers'),
    ]

    user_permissions_list = [
        ('can_manage_users', 'Manage Users', 'Access user management'),
    ]

    if request.method == 'POST':
        # Update inventory permissions
        for field, _, _ in inventory_permissions:
            setattr(user, field, field in request.POST)

        # Update billing permissions
        for field, _, _ in billing_permissions:
            setattr(user, field, field in request.POST)

        # Update user management permissions
        for field, _, _ in user_permissions_list:
            setattr(user, field, field in request.POST)

        user.save()
        messages.success(request, f'Permissions updated for {user.username}.')
        return redirect('user_permissions', pk=pk)

    context = {
        'edit_user': user,
        'inventory_permissions': inventory_permissions,
        'billing_permissions': billing_permissions,
        'user_permissions_list': user_permissions_list,
    }
    return render(request, 'accounts/user_permissions.html', context)

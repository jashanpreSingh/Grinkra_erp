from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q, Sum, F
from functools import wraps
from .models import Category, Product
from .forms import CategoryForm, ProductForm, StockAdjustmentForm


def permission_required(permission_attr, redirect_url='dashboard'):
    """Decorator to check user permissions"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            # Admins have all permissions
            if user.is_admin():
                return view_func(request, *args, **kwargs)
            # Check specific permission
            if getattr(user, permission_attr, False):
                return view_func(request, *args, **kwargs)
            messages.error(request, 'You do not have permission to access this page.')
            return redirect(redirect_url)
        return login_required(wrapper)
    return decorator


@login_required
def product_list(request):
    if not request.user.can_view_inventory and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view inventory.')
        return redirect('dashboard')
    
    products = Product.objects.select_related('category').all()

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Category filter
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)

    # Stock status filter
    stock_status = request.GET.get('stock_status', '')
    if stock_status == 'low_stock':
        products = products.filter(quantity__gt=0, quantity__lte=F('low_stock_threshold'))
    elif stock_status == 'out_of_stock':
        products = products.filter(quantity=0)
    elif stock_status == 'in_stock':
        products = products.filter(quantity__gt=F('low_stock_threshold'))

    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_stock_status': stock_status,
    }
    return render(request, 'inventory/product_list.html', context)


@permission_required('can_add_product')
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully.')
            return redirect('product_list')
    else:
        form = ProductForm()

    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Add Product'})


@permission_required('can_edit_product')
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Edit Product', 'product': product})


@permission_required('can_delete_product')
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('product_list')


@permission_required('can_adjust_stock')
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    stock_form = StockAdjustmentForm()

    if request.method == 'POST':
        stock_form = StockAdjustmentForm(request.POST)
        if stock_form.is_valid():
            adjustment_type = stock_form.cleaned_data['adjustment_type']
            quantity = stock_form.cleaned_data['quantity']
            reason = stock_form.cleaned_data['reason']

            try:
                if adjustment_type == 'remove':
                    quantity = -quantity
                product.adjust_stock(quantity, reason)
                messages.success(request, f'Stock adjusted successfully. New quantity: {product.quantity}')
            except ValueError as e:
                messages.error(request, str(e))

            return redirect('product_detail', pk=pk)

    return render(request, 'inventory/product_detail.html', {
        'product': product,
        'stock_form': stock_form
    })


@login_required
def category_list(request):
    if not request.user.can_view_inventory and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view inventory.')
        return redirect('dashboard')
    
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})


@permission_required('can_manage_categories')
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm()

    return render(request, 'inventory/category_form.html', {'form': form, 'title': 'Add Category'})


@permission_required('can_manage_categories')
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'inventory/category_form.html', {'form': form, 'title': 'Edit Category'})


@permission_required('can_manage_categories')
@require_POST
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if category.products.exists():
        messages.error(request, 'Cannot delete category with associated products.')
    else:
        category.delete()
        messages.success(request, 'Category deleted successfully.')
    return redirect('category_list')

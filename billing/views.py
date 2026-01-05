from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.db import transaction
from decimal import Decimal
from .models import Customer, Invoice, InvoiceItem
from .forms import CustomerForm, InvoiceForm, InvoiceItemForm, InvoicePaymentForm
from inventory.models import Product


@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('customer', 'created_by').all()

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(customer_name__icontains=search_query)
        )

    # Status filter
    status = request.GET.get('status', '')
    if status:
        invoices = invoices.filter(status=status)

    context = {
        'invoices': invoices,
        'search_query': search_query,
        'selected_status': status,
    }
    return render(request, 'billing/invoice_list.html', context)


@login_required
def invoice_create(request):
    products = Product.objects.filter(is_active=True, quantity__gt=0)
    customers = Customer.objects.all()

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                invoice = form.save(commit=False)
                invoice.created_by = request.user
                invoice.save()

                # Process items
                product_ids = request.POST.getlist('product_id')
                quantities = request.POST.getlist('quantity')
                prices = request.POST.getlist('unit_price')

                for i, product_id in enumerate(product_ids):
                    if product_id and quantities[i]:
                        product = Product.objects.get(pk=product_id)
                        quantity = int(quantities[i])
                        price = Decimal(prices[i]) if prices[i] else product.price

                        # Deduct stock
                        if product.quantity < quantity:
                            messages.error(request, f'Insufficient stock for {product.name}')
                            invoice.delete()
                            return redirect('invoice_create')

                        product.adjust_stock(-quantity, f'Invoice #{invoice.invoice_number}')

                        InvoiceItem.objects.create(
                            invoice=invoice,
                            product=product,
                            product_name=product.name,
                            quantity=quantity,
                            unit_price=price
                        )

                invoice.calculate_totals()
                messages.success(request, f'Invoice {invoice.invoice_number} created successfully.')
                return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm()

    return render(request, 'billing/invoice_form.html', {
        'form': form,
        'products': products,
        'customers': customers,
        'title': 'Create Invoice'
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.prefetch_related('items'), pk=pk)
    payment_form = InvoicePaymentForm(initial={
        'amount_paid': invoice.balance_due,
        'payment_method': invoice.payment_method
    })

    if request.method == 'POST' and 'mark_paid' in request.POST:
        payment_form = InvoicePaymentForm(request.POST)
        if payment_form.is_valid():
            invoice.amount_paid += payment_form.cleaned_data['amount_paid']
            invoice.payment_method = payment_form.cleaned_data['payment_method']
            if invoice.amount_paid >= invoice.total_amount:
                invoice.status = 'paid'
            invoice.save()
            messages.success(request, 'Payment recorded successfully.')
            return redirect('invoice_detail', pk=pk)

    return render(request, 'billing/invoice_detail.html', {
        'invoice': invoice,
        'payment_form': payment_form
    })


@login_required
@require_POST
def invoice_cancel(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.status == 'cancelled':
        messages.error(request, 'Invoice is already cancelled.')
    else:
        with transaction.atomic():
            # Restore stock
            for item in invoice.items.all():
                if item.product:
                    item.product.adjust_stock(item.quantity, f'Invoice #{invoice.invoice_number} cancelled')

            invoice.status = 'cancelled'
            invoice.save()
            messages.success(request, 'Invoice cancelled and stock restored.')

    return redirect('invoice_detail', pk=pk)


@login_required
def customer_list(request):
    customers = Customer.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    return render(request, 'billing/customer_list.html', {
        'customers': customers,
        'search_query': search_query
    })


@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer created successfully.')
            return redirect('customer_list')
    else:
        form = CustomerForm()

    return render(request, 'billing/customer_form.html', {'form': form, 'title': 'Add Customer'})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully.')
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'billing/customer_form.html', {'form': form, 'title': 'Edit Customer'})


@login_required
@require_POST
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if customer.invoices.exists():
        messages.error(request, 'Cannot delete customer with associated invoices.')
    else:
        customer.delete()
        messages.success(request, 'Customer deleted successfully.')
    return redirect('customer_list')


@login_required
def get_product_price(request, pk):
    """API endpoint to get product price for invoice form."""
    product = get_object_or_404(Product, pk=pk)
    return JsonResponse({
        'price': str(product.price),
        'stock': product.quantity
    })

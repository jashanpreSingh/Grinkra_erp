from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json


@login_required
def dashboard(request):
    # Import here to avoid circular imports
    from inventory.models import Product, Category
    from billing.models import Invoice, Customer, InvoiceItem

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_start = today.replace(day=1)
    six_months_ago = today - timedelta(days=180)
    thirty_days_ago = today - timedelta(days=30)

    # Product stats
    total_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(
        is_active=True,
        quantity__gt=0,
        quantity__lte=F('low_stock_threshold')
    )
    out_of_stock_products = Product.objects.filter(is_active=True, quantity=0)

    # Invoice stats
    today_invoices = Invoice.objects.filter(
        created_at__date=today,
        status__in=['pending', 'paid']
    )
    today_sales = today_invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    today_invoice_count = today_invoices.count()

    month_invoices = Invoice.objects.filter(
        created_at__date__gte=month_start,
        status__in=['pending', 'paid']
    )
    month_sales = month_invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    pending_invoices = Invoice.objects.filter(status='pending')
    pending_amount = pending_invoices.aggregate(
        total=Sum(F('total_amount') - F('amount_paid'))
    )['total'] or Decimal('0.00')

    # Customer stats
    total_customers = Customer.objects.count()

    # Recent invoices
    recent_invoices = Invoice.objects.select_related('customer').order_by('-created_at')[:5]

    # Low stock alerts
    low_stock_list = low_stock_products.order_by('quantity')[:5]

    # ===== DAILY SALES (Last 7 days) =====
    daily_sales_data = Invoice.objects.filter(
        created_at__date__gte=week_ago,
        status__in=['pending', 'paid']
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('total_amount')
    ).order_by('date')

    # Fill in missing days with zero
    daily_labels = []
    daily_data = []
    sales_dict = {item['date']: float(item['total']) for item in daily_sales_data}
    for i in range(7):
        day = week_ago + timedelta(days=i)
        daily_labels.append(day.strftime('%b %d'))
        daily_data.append(sales_dict.get(day, 0))

    # ===== WEEKLY SALES (Last 4 weeks) =====
    four_weeks_ago = today - timedelta(weeks=4)
    weekly_sales_data = Invoice.objects.filter(
        created_at__date__gte=four_weeks_ago,
        status__in=['pending', 'paid']
    ).annotate(
        week=TruncWeek('created_at')
    ).values('week').annotate(
        total=Sum('total_amount')
    ).order_by('week')

    weekly_labels = []
    weekly_data = []
    for item in weekly_sales_data:
        week_start = item['week'].date() if hasattr(item['week'], 'date') else item['week']
        weekly_labels.append(f"Week of {week_start.strftime('%b %d')}")
        weekly_data.append(float(item['total']))

    # ===== MONTHLY SALES (Last 6 months) =====
    monthly_sales_data = Invoice.objects.filter(
        created_at__date__gte=six_months_ago,
        status__in=['pending', 'paid']
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')

    monthly_labels = []
    monthly_data = []
    for item in monthly_sales_data:
        month_date = item['month'].date() if hasattr(item['month'], 'date') else item['month']
        monthly_labels.append(month_date.strftime('%b %Y'))
        monthly_data.append(float(item['total']))

    # ===== TOP MOVING PRODUCTS (Last 30 days) =====
    moving_products = InvoiceItem.objects.filter(
        invoice__created_at__date__gte=thirty_days_ago,
        invoice__status__in=['pending', 'paid']
    ).values(
        'product_name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('total')
    ).order_by('-total_qty')[:10]

    moving_labels = [item['product_name'][:20] for item in moving_products]
    moving_qty_data = [item['total_qty'] for item in moving_products]
    moving_revenue_data = [float(item['total_revenue']) for item in moving_products]

    # ===== NON-MOVING PRODUCTS (No sales in last 30 days) =====
    sold_product_ids = InvoiceItem.objects.filter(
        invoice__created_at__date__gte=thirty_days_ago,
        invoice__status__in=['pending', 'paid'],
        product__isnull=False
    ).values_list('product_id', flat=True).distinct()

    non_moving_products = Product.objects.filter(
        is_active=True
    ).exclude(
        id__in=sold_product_ids
    ).order_by('-quantity')[:10]

    non_moving_labels = [p.name[:20] for p in non_moving_products]
    non_moving_stock = [p.quantity for p in non_moving_products]

    context = {
        # Stats
        'total_products': total_products,
        'low_stock_count': low_stock_products.count(),
        'out_of_stock_count': out_of_stock_products.count(),
        'today_sales': today_sales,
        'today_invoice_count': today_invoice_count,
        'month_sales': month_sales,
        'pending_count': pending_invoices.count(),
        'pending_amount': pending_amount,
        'total_customers': total_customers,

        # Lists
        'recent_invoices': recent_invoices,
        'low_stock_list': low_stock_list,

        # Chart data as JSON for JavaScript
        'daily_labels': json.dumps(daily_labels),
        'daily_data': json.dumps(daily_data),
        'weekly_labels': json.dumps(weekly_labels),
        'weekly_data': json.dumps(weekly_data),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data),
        'moving_labels': json.dumps(moving_labels),
        'moving_qty_data': json.dumps(moving_qty_data),
        'moving_revenue_data': json.dumps(moving_revenue_data),
        'non_moving_labels': json.dumps(non_moving_labels),
        'non_moving_stock': json.dumps(non_moving_stock),
        'non_moving_count': len(non_moving_labels),
        'moving_count': len(moving_labels),
    }
    return render(request, 'dashboard/dashboard.html', context)

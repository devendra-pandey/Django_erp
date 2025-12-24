from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
import json
from datetime import datetime, timedelta
import csv
import openpyxl
from openpyxl import Workbook
from io import BytesIO

@login_required
def report_dashboard(request):
    """Reports dashboard"""
    return render(request, 'reports/dashboard.html')

@login_required
def inventory_report(request):
    """Inventory report"""
    from inventory.models import Stock, Product, Warehouse, Category
    
    stocks = Stock.objects.select_related('product', 'warehouse', 'product__category').all()
    
    # Apply filters
    warehouse_id = request.GET.get('warehouse')
    if warehouse_id:
        stocks = stocks.filter(warehouse_id=warehouse_id)
    
    category_id = request.GET.get('category')
    if category_id:
        stocks = stocks.filter(product__category_id=category_id)
    
    low_stock = request.GET.get('low_stock') == 'true'
    if low_stock:
        stocks = stocks.filter(quantity__lt=models.F('product__min_stock'))
    
    format = request.GET.get('format', 'html')
    
    if format == 'excel':
        return generate_inventory_excel(stocks)
    elif format == 'csv':
        return generate_inventory_csv(stocks)
    else:
        context = {
            'stocks': stocks,
            'warehouses': Warehouse.objects.all(),
            'categories': Category.objects.all(),
        }
        return render(request, 'reports/inventory_report.html', context)

@login_required
def low_stock_report(request):
    """Low stock report"""
    from inventory.models import Stock, Product
    
    low_stock_items = Stock.objects.select_related('product', 'warehouse').filter(
        quantity__lt=models.F('product__min_stock')
    )
    
    format = request.GET.get('format', 'html')
    
    if format == 'excel':
        return generate_low_stock_excel(low_stock_items)
    else:
        context = {
            'low_stock_items': low_stock_items,
        }
        return render(request, 'reports/low_stock_report.html', context)

@login_required
def stock_movement_report(request):
    """Stock movement report"""
    from inventory.models import StockTransaction
    
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    movements = StockTransaction.objects.filter(
        created_at__range=[start_date, end_date]
    ).select_related('product', 'warehouse')
    
    context = {
        'movements': movements,
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'reports/stock_movement_report.html', context)

@login_required
def abc_analysis_report(request):
    """ABC Analysis report"""
    from inventory.models import Product
    
    # Simplified ABC analysis
    products = Product.objects.annotate(
        stock_value=Sum('stock__quantity')
    ).filter(stock_value__isnull=False).order_by('-stock_value')
    
    context = {
        'products': products,
    }
    return render(request, 'reports/abc_analysis_report.html', context)

@login_required
def production_report(request):
    """Production report"""
    from production.models import ProductionOrder
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')
    
    orders = ProductionOrder.objects.select_related('product', 'bom').all()
    
    if start_date:
        orders = orders.filter(planned_start__date__gte=start_date)
    if end_date:
        orders = orders.filter(planned_end__date__lte=end_date)
    if status:
        orders = orders.filter(status=status)
    
    # Calculate metrics
    total_orders = orders.count()
    completed_orders = orders.filter(status='completed').count()
    total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0
    completed_quantity = orders.filter(status='completed').aggregate(total=Sum('completed_quantity'))['total'] or 0
    
    context = {
        'orders': orders,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'total_quantity': total_quantity,
        'completed_quantity': completed_quantity,
        'completion_rate': (completed_orders / total_orders * 100) if total_orders > 0 else 0,
    }
    
    return render(request, 'reports/production_report.html', context)

@login_required
def production_efficiency_report(request):
    """Production efficiency report"""
    from production.models import ProductionOrder
    
    # Simplified efficiency report
    orders = ProductionOrder.objects.filter(status='completed').select_related('product')
    
    context = {
        'orders': orders,
    }
    return render(request, 'reports/production_efficiency_report.html', context)

@login_required
def downtime_report(request):
    """Downtime report"""
    # Simplified downtime report
    return render(request, 'reports/downtime_report.html')

@login_required
def rejection_report(request):
    """Rejection report"""
    from production.models import ProductionOrder
    
    orders = ProductionOrder.objects.filter(rejected_quantity__gt=0).select_related('product')
    
    total_produced = orders.aggregate(total=Sum('completed_quantity'))['total'] or 0
    total_rejected = orders.aggregate(total=Sum('rejected_quantity'))['total'] or 0
    rejection_rate = (total_rejected / total_produced * 100) if total_produced > 0 else 0
    
    context = {
        'orders': orders,
        'total_produced': total_produced,
        'total_rejected': total_rejected,
        'rejection_rate': rejection_rate,
    }
    return render(request, 'reports/rejection_report.html', context)

@login_required
def quality_report(request):
    """Quality report"""
    from quality.models import QualityCheck
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    checks = QualityCheck.objects.all()
    
    if start_date:
        checks = checks.filter(inspection_date__gte=start_date)
    if end_date:
        checks = checks.filter(inspection_date__lte=end_date)
    
    passed = checks.filter(status='passed').count()
    failed = checks.filter(status='failed').count()
    total = checks.count()
    
    context = {
        'checks': checks,
        'passed': passed,
        'failed': failed,
        'total': total,
        'quality_rate': (passed / total * 100) if total > 0 else 0,
    }
    
    return render(request, 'reports/quality_report.html', context)

@login_required
def defect_analysis_report(request):
    """Defect analysis report"""
    from quality.models import QualityCheck, NonConformanceReport
    
    ncrs = NonConformanceReport.objects.all().select_related('quality_check')
    
    # Group by severity
    severity_counts = ncrs.values('severity').annotate(count=Count('id')).order_by('-count')
    
    context = {
        'ncrs': ncrs,
        'severity_counts': severity_counts,
    }
    
    return render(request, 'reports/defect_analysis_report.html', context)

@login_required
def quality_trends_report(request):
    """Quality trends report"""
    from quality.models import QualityCheck
    
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    trends = QualityCheck.objects.filter(
        inspection_date__range=[start_date, end_date]
    ).values('inspection_date').annotate(
        total=Count('id'),
        passed=Count('id', filter=Q(status='passed')),
        failed=Count('id', filter=Q(status='failed'))
    ).order_by('inspection_date')
    
    context = {
        'trends': list(trends),
        'days': days,
    }
    
    return render(request, 'reports/quality_trends_report.html', context)

@login_required
def hr_attendance_report(request):
    """HR attendance report"""
    from hr.models import Attendance, Employee
    
    month = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    year, month_num = map(int, month.split('-'))
    
    attendances = Attendance.objects.filter(
        date__year=year,
        date__month=month_num
    ).select_related('employee')
    
    context = {
        'attendances': attendances,
        'month': month,
    }
    
    return render(request, 'reports/hr_attendance_report.html', context)

@login_required
def hr_leave_report(request):
    """HR leave report"""
    from hr.models import LeaveApplication
    
    month = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    year, month_num = map(int, month.split('-'))
    
    leaves = LeaveApplication.objects.filter(
        created_at__year=year,
        created_at__month=month_num
    ).select_related('employee', 'leave_type')
    
    context = {
        'leaves': leaves,
        'month': month,
    }
    
    return render(request, 'reports/hr_leave_report.html', context)

@login_required
def hr_overtime_report(request):
    """HR overtime report"""
    from hr.models import Attendance
    
    month = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    year, month_num = map(int, month.split('-'))
    
    overtime_data = Attendance.objects.filter(
        date__year=year,
        date__month=month_num,
        overtime_hours__gt=0
    ).select_related('employee').order_by('-overtime_hours')
    
    total_overtime = sum(float(item.overtime_hours) for item in overtime_data)
    
    context = {
        'overtime_data': overtime_data,
        'month': month,
        'total_overtime': total_overtime,
    }
    
    return render(request, 'reports/hr_overtime_report.html', context)

@login_required
def purchase_report(request):
    """Purchase report"""
    from procurement.models import PurchaseOrder
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    orders = PurchaseOrder.objects.select_related('supplier').all()
    
    if start_date:
        orders = orders.filter(order_date__gte=start_date)
    if end_date:
        orders = orders.filter(order_date__lte=end_date)
    
    total_amount = orders.aggregate(total=Sum('grand_total'))['total'] or 0
    
    context = {
        'orders': orders,
        'total_amount': total_amount,
    }
    
    return render(request, 'reports/purchase_report.html', context)

@login_required
def inventory_value_report(request):
    """Inventory value report"""
    from inventory.models import Stock, Product
    
    # Simplified inventory value calculation
    stocks = Stock.objects.select_related('product').all()
    
    total_value = 0
    for stock in stocks:
        # Assuming product has a cost field
        if hasattr(stock.product, 'standard_cost'):
            total_value += float(stock.quantity) * float(stock.product.standard_cost or 0)
    
    context = {
        'stocks': stocks,
        'total_value': total_value,
    }
    
    return render(request, 'reports/inventory_value_report.html', context)

@login_required
def create_custom_report(request):
    """Create custom report"""
    return render(request, 'reports/create_custom_report.html')

@login_required
def saved_reports_list(request):
    """List of saved reports"""
    # Simplified version
    return render(request, 'reports/saved_reports_list.html')

@login_required
def view_saved_report(request, pk):
    """View saved report"""
    # Simplified version
    return render(request, 'reports/view_saved_report.html')

@login_required
def download_saved_report(request, pk):
    """Download saved report"""
    # Simplified version
    return HttpResponse("Download feature coming soon")

# Helper functions for Excel/CSV export
def generate_inventory_excel(stocks):
    """Generate Excel file for inventory report"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventory Report"
    
    # Add headers
    headers = ['SKU', 'Product Name', 'Warehouse', 'Quantity', 'Min Stock', 'Max Stock', 'Status']
    ws.append(headers)
    
    # Add data
    for stock in stocks:
        status = 'Low' if stock.quantity < stock.product.min_stock else 'OK'
        ws.append([
            stock.product.SKU,
            stock.product.name,
            stock.warehouse.name,
            float(stock.quantity),
            float(stock.product.min_stock),
            float(stock.product.max_stock),
            status
        ])
    
    # Create response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=inventory_report.xlsx'
    
    wb.save(response)
    return response

def generate_inventory_csv(stocks):
    """Generate CSV file for inventory report"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=inventory_report.csv'
    
    writer = csv.writer(response)
    writer.writerow(['SKU', 'Product Name', 'Warehouse', 'Quantity', 'Min Stock', 'Max Stock', 'Status'])
    
    for stock in stocks:
        status = 'Low' if stock.quantity < stock.product.min_stock else 'OK'
        writer.writerow([
            stock.product.SKU,
            stock.product.name,
            stock.warehouse.name,
            stock.quantity,
            stock.product.min_stock,
            stock.product.max_stock,
            status
        ])
    
    return response

def generate_low_stock_excel(low_stock_items):
    """Generate Excel file for low stock report"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Low Stock Report"
    
    # Add headers
    headers = ['SKU', 'Product Name', 'Warehouse', 'Current Stock', 'Min Stock', 'Deficit']
    ws.append(headers)
    
    # Add data
    for item in low_stock_items:
        deficit = item.product.min_stock - item.quantity
        ws.append([
            item.product.SKU,
            item.product.name,
            item.warehouse.name,
            float(item.quantity),
            float(item.product.min_stock),
            float(deficit)
        ])
    
    # Create response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=low_stock_report.xlsx'
    
    wb.save(response)
    return response
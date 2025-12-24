from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
import json
from datetime import datetime, timedelta

@login_required
def analytics_dashboard(request):
    """Analytics dashboard"""
    return render(request, 'analytics/dashboard.html')

@login_required
def production_analytics(request):
    """Production analytics API"""
    from production.models import ProductionOrder
    
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Production data
    orders = ProductionOrder.objects.filter(
        planned_start__range=[start_date, end_date]
    )
    
    # Daily production summary
    daily_data = orders.filter(status='completed').values(
        'actual_end__date'
    ).annotate(
        total_quantity=Sum('completed_quantity'),
        total_orders=Count('id')
    ).order_by('actual_end__date')
    
    # Status distribution
    status_distribution = orders.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Product-wise production
    product_data = orders.values('product__name').annotate(
        total_quantity=Sum('quantity'),
        completed_quantity=Sum('completed_quantity')
    ).order_by('-total_quantity')[:10]
    
    return JsonResponse({
        'daily_data': list(daily_data),
        'status_distribution': list(status_distribution),
        'product_data': list(product_data),
    })

@login_required
def inventory_analytics(request):
    """Inventory analytics API"""
    from inventory.models import Stock, Product
    
    # Inventory metrics
    total_items = Product.objects.count()
    total_value = 0  # Simplified calculation
    
    # Stock status
    stock_status = Stock.objects.aggregate(
        low_stock=Count('id', filter=Q(quantity__lt=models.F('product__min_stock'))),
        normal_stock=Count('id', filter=Q(quantity__gte=models.F('product__min_stock'))),
        out_of_stock=Count('id', filter=Q(quantity=0))
    )
    
    # Category distribution
    category_distribution = Product.objects.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    return JsonResponse({
        'total_items': total_items,
        'total_value': total_value,
        'stock_status': stock_status,
        'category_distribution': list(category_distribution),
    })

@login_required
def quality_analytics(request):
    """Quality analytics API"""
    from quality.models import QualityCheck
    
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Quality trends
    quality_trends = QualityCheck.objects.filter(
        inspection_date__range=[start_date, end_date]
    ).values('inspection_date').annotate(
        total=Count('id'),
        passed=Count('id', filter=Q(status='passed')),
        failed=Count('id', filter=Q(status='failed'))
    ).order_by('inspection_date')
    
    # Overall quality metrics
    total_checks = QualityCheck.objects.count()
    passed_checks = QualityCheck.objects.filter(status='passed').count()
    quality_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    # Check type distribution
    type_distribution = QualityCheck.objects.values('qc_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return JsonResponse({
        'quality_trends': list(quality_trends),
        'total_checks': total_checks,
        'passed_checks': passed_checks,
        'quality_rate': quality_rate,
        'type_distribution': list(type_distribution),
    })

@login_required
def financial_analytics(request):
    """Financial analytics API"""
    from procurement.models import PurchaseOrder
    
    days = int(request.GET.get('days', 90))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Purchase analytics
    purchases = PurchaseOrder.objects.filter(
        order_date__range=[start_date, end_date],
        status__in=['received', 'partial']
    )
    
    # Monthly spending
    monthly_spending = purchases.values(
        'order_date__year', 'order_date__month'
    ).annotate(
        total_amount=Sum('grand_total'),
        count=Count('id')
    ).order_by('order_date__year', 'order_date__month')
    
    # Supplier spending
    supplier_spending = purchases.values('supplier__name').annotate(
        total_amount=Sum('grand_total'),
        order_count=Count('id')
    ).order_by('-total_amount')[:10]
    
    return JsonResponse({
        'monthly_spending': list(monthly_spending),
        'supplier_spending': list(supplier_spending),
        'total_spending': purchases.aggregate(total=Sum('grand_total'))['total'] or 0,
    })

@login_required
def hr_analytics(request):
    """HR analytics API"""
    from hr.models import Employee, Attendance, LeaveApplication
    
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Employee statistics
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(employment_status='active').count()
    
    # Attendance trends
    attendance_trends = Attendance.objects.filter(
        date__range=[start_date, end_date]
    ).values('date').annotate(
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent'))
    ).order_by('date')
    
    # Leave trends
    leave_trends = LeaveApplication.objects.filter(
        created_at__range=[start_date, end_date]
    ).values('created_at__date').annotate(
        count=Count('id')
    ).order_by('created_at__date')
    
    # Department distribution
    department_distribution = Employee.objects.values('department__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return JsonResponse({
        'total_employees': total_employees,
        'active_employees': active_employees,
        'attendance_trends': list(attendance_trends),
        'leave_trends': list(leave_trends),
        'department_distribution': list(department_distribution),
    })

@login_required
def real_time_metrics(request):
    """Real-time metrics API"""
    from production.models import ProductionOrder
    from inventory.models import Stock
    from quality.models import QualityCheck
    from hr.models import Attendance
    
    now = timezone.now()
    today = now.date()
    
    # Active production orders
    active_orders = ProductionOrder.objects.filter(
        status__in=['in_progress', 'released']
    ).count()
    
    # Today's production
    today_production = ProductionOrder.objects.filter(
        actual_end__date=today,
        status='completed'
    ).aggregate(
        total=Sum('completed_quantity')
    )['total'] or 0
    
    # Low stock items
    low_stock = Stock.objects.filter(
        quantity__lt=models.F('product__min_stock')
    ).count()
    
    # Pending quality checks
    pending_qc = QualityCheck.objects.filter(status='pending').count()
    
    # Today's attendance
    today_attendance = Attendance.objects.filter(date=today).aggregate(
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
        late=Count('id', filter=Q(check_in__gt='09:00'))
    )
    
    return JsonResponse({
        'active_orders': active_orders,
        'today_production': today_production,
        'low_stock_items': low_stock,
        'pending_qc': pending_qc,
        'attendance': today_attendance,
        'timestamp': now.isoformat(),
    })

@login_required
def live_production_data(request):
    """Live production data API"""
    from production.models import ProductionOrder
    
    active_orders = ProductionOrder.objects.filter(
        status__in=['in_progress']
    ).select_related('product').values(
        'order_number', 'product__name', 'quantity', 'completed_quantity'
    )[:10]
    
    recent_completed = ProductionOrder.objects.filter(
        status='completed'
    ).order_by('-actual_end').select_related('product').values(
        'order_number', 'product__name', 'completed_quantity', 'actual_end'
    )[:5]
    
    return JsonResponse({
        'active_orders': list(active_orders),
        'recent_completed': list(recent_completed),
    })

@login_required
def production_analytics_dashboard(request):
    """Production analytics dashboard"""
    return render(request, 'analytics/production_dashboard.html')

@login_required
def inventory_analytics_dashboard(request):
    """Inventory analytics dashboard"""
    return render(request, 'analytics/inventory_dashboard.html')

@login_required
def quality_analytics_dashboard(request):
    """Quality analytics dashboard"""
    return render(request, 'analytics/quality_dashboard.html')

@login_required
def financial_analytics_dashboard(request):
    """Financial analytics dashboard"""
    return render(request, 'analytics/financial_dashboard.html')

@login_required
def production_trends(request):
    """Production trends analysis"""
    return render(request, 'analytics/production_trends.html')

@login_required
def quality_trends(request):
    """Quality trends analysis"""
    return render(request, 'analytics/quality_trends.html')

@login_required
def inventory_trends(request):
    """Inventory trends analysis"""
    return render(request, 'analytics/inventory_trends.html')
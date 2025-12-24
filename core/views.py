from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, F  # Add F here
from django.utils import timezone
from datetime import datetime, timedelta

@login_required
def dashboard(request):
    """Main dashboard view"""
    # Import models inside function to avoid circular imports
    try:
        from production.models import ProductionOrder
        from inventory.models import Stock
        from quality.models import QualityCheck
        from hr.models import Attendance
        from procurement.models import PurchaseOrder
    except ImportError:
        # If some apps aren't installed yet, use dummy data
        active_orders = 0
        today_production = 0
        low_stock_items = 0
        pending_qc = 0
        recent_orders = []
        low_stock_list = []
        today_attendance = {'present': 0, 'absent': 0}
        pending_purchase_orders = 0
        
        context = {
            'active_orders': active_orders,
            'today_production': today_production,
            'low_stock_items': low_stock_items,
            'pending_qc': pending_qc,
            'recent_orders': recent_orders,
            'low_stock_list': low_stock_list,
            'today_attendance': today_attendance,
            'pending_purchase_orders': pending_purchase_orders,
        }
        return render(request, 'dashboard.html', context)
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    try:
        # Production metrics
        active_orders = ProductionOrder.objects.filter(
            status__in=['in_progress', 'released']
        ).count()
        
        # Today's production
        today_production = ProductionOrder.objects.filter(
            status='completed',
            actual_end__date=today
        ).aggregate(total=Sum('completed_quantity'))['total'] or 0
        
        # Low stock items
        low_stock_items = Stock.objects.filter(
            quantity__lt=F('product__min_stock')  # Use F() here
        ).count()
        
        # Pending quality checks
        pending_qc = QualityCheck.objects.filter(status='pending').count()
        
        # Recent orders
        recent_orders = ProductionOrder.objects.select_related(
            'product', 'uom'
        ).order_by('-created_at')[:5]
        
        # Low stock list
        low_stock_list = Stock.objects.filter(
            quantity__lt=F('product__min_stock')  # Use F() here
        ).select_related('product', 'warehouse')[:5]
        
        # Today's attendance
        today_attendance = Attendance.objects.filter(date=today).aggregate(
            present=Count('id', filter=Q(status='present')),
            absent=Count('id', filter=Q(status='absent'))
        )
        
        # Pending purchase orders
        pending_purchase_orders = PurchaseOrder.objects.filter(
            status__in=['draft', 'sent', 'confirmed']
        ).count()
        
    except Exception as e:
        # If there's any database error (tables not created yet), use dummy data
        print(f"Dashboard error: {e}")  # For debugging
        active_orders = 0
        today_production = 0
        low_stock_items = 0
        pending_qc = 0
        recent_orders = []
        low_stock_list = []
        today_attendance = {'present': 0, 'absent': 0}
        pending_purchase_orders = 0
    
    context = {
        'active_orders': active_orders,
        'today_production': today_production,
        'low_stock_items': low_stock_items,
        'pending_qc': pending_qc,
        'recent_orders': recent_orders,
        'low_stock_list': low_stock_list,
        'today_attendance': today_attendance,
        'pending_purchase_orders': pending_purchase_orders,
    }
    
    return render(request, 'dashboard.html', context)
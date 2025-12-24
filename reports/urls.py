from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_dashboard, name='dashboard'),
    
    # Inventory Reports
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('inventory/low-stock/', views.low_stock_report, name='low_stock_report'),
    path('inventory/stock-movement/', views.stock_movement_report, name='stock_movement_report'),
    path('inventory/abc-analysis/', views.abc_analysis_report, name='abc_analysis_report'),
    
    # Production Reports
    path('production/', views.production_report, name='production_report'),
    path('production/efficiency/', views.production_efficiency_report, name='production_efficiency_report'),
    path('production/downtime/', views.downtime_report, name='downtime_report'),
    path('production/rejection/', views.rejection_report, name='rejection_report'),
    
    # Quality Reports
    path('quality/', views.quality_report, name='quality_report'),
    path('quality/defect-analysis/', views.defect_analysis_report, name='defect_analysis'),
    path('quality/quality-trends/', views.quality_trends_report, name='quality_trends'),
    
    # HR Reports
    path('hr/attendance/', views.hr_attendance_report, name='hr_attendance_report'),
    path('hr/leave/', views.hr_leave_report, name='hr_leave_report'),
    path('hr/overtime/', views.hr_overtime_report, name='hr_overtime_report'),
    
    # Financial Reports
    path('financial/purchase/', views.purchase_report, name='purchase_report'),
    path('financial/inventory-value/', views.inventory_value_report, name='inventory_value_report'),
    
    # Custom Reports
    path('custom/create/', views.create_custom_report, name='create_custom_report'),
    path('custom/saved/', views.saved_reports_list, name='saved_reports'),
    path('custom/<int:pk>/', views.view_saved_report, name='view_saved_report'),
    path('custom/<int:pk>/download/', views.download_saved_report, name='download_saved_report'),
]
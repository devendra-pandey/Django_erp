from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    
    # Data APIs
    path('api/production-metrics/', views.production_analytics, name='production_metrics'),
    path('api/inventory-metrics/', views.inventory_analytics, name='inventory_metrics'),
    path('api/quality-metrics/', views.quality_analytics, name='quality_metrics'),
    path('api/financial-metrics/', views.financial_analytics, name='financial_metrics'),
    path('api/hr-metrics/', views.hr_analytics, name='hr_metrics'),
    
    # Real-time Updates
    path('api/real-time-metrics/', views.real_time_metrics, name='real_time_metrics'),
    path('api/live-production/', views.live_production_data, name='live_production'),
    
    # Dashboards
    path('production/', views.production_analytics_dashboard, name='production_dashboard'),
    path('inventory/', views.inventory_analytics_dashboard, name='inventory_dashboard'),
    path('quality/', views.quality_analytics_dashboard, name='quality_dashboard'),
    path('financial/', views.financial_analytics_dashboard, name='financial_dashboard'),
    
    # Trends Analysis
    path('trends/production/', views.production_trends, name='production_trends'),
    path('trends/quality/', views.quality_trends, name='quality_trends'),
    path('trends/inventory/', views.inventory_trends, name='inventory_trends'),
]
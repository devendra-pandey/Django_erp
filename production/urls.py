from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    # BOM URLs
    path('bom/', views.BOMListView.as_view(), name='bom_list'),
    path('bom/create/', views.BOMCreateView.as_view(), name='bom_create'),
    path('bom/<int:pk>/', views.BOMDetailView.as_view(), name='bom_detail'),
    path('bom/<int:pk>/update/', views.BOMUpdateView.as_view(), name='bom_update'),
    path('bom/<int:pk>/delete/', views.BOMDeleteView.as_view(), name='bom_delete'),
    
    # Production Order URLs
    path('orders/', views.ProductionOrderListView.as_view(), name='order_list'),
    path('orders/create/', views.ProductionOrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', views.ProductionOrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/update/', views.ProductionOrderUpdateView.as_view(), name='order_update'),
    path('orders/<int:pk>/delete/', views.ProductionOrderDeleteView.as_view(), name='order_delete'),
    path('orders/<int:pk>/start/', views.start_production_order, name='order_start'),
    path('orders/<int:pk>/complete/', views.complete_production_order, name='order_complete'),
    
    # Work Center URLs
    path('work-centers/', views.WorkCenterListView.as_view(), name='workcenter_list'),
    path('work-centers/create/', views.WorkCenterCreateView.as_view(), name='workcenter_create'),
    
    # Operation URLs
    path('operations/', views.OperationListView.as_view(), name='operation_list'),
    path('operations/create/', views.OperationCreateView.as_view(), name='operation_create'),
    
    # Production Dashboard
    path('dashboard/', views.production_dashboard, name='dashboard'),
    
    # Material Issue URLs
    path('material-issue/<int:order_id>/', views.material_issue_view, name='material_issue'),
    
    # Production Operation URLs
    path('operations/start/<int:pk>/', views.start_operation, name='operation_start'),
    path('operations/complete/<int:pk>/', views.complete_operation, name='operation_complete'),
]
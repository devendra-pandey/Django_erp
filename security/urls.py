from django.urls import path
from . import views

urlpatterns = [
    # Gate Pass URLs
    path('', views.GatePassListView.as_view(), name='gatepass_list'),
    path('create/', views.GatePassCreateView.as_view(), name='gatepass_create'),
    path('<int:pk>/', views.GatePassDetailView.as_view(), name='gatepass_detail'),
    path('<int:pk>/edit/', views.GatePassUpdateView.as_view(), name='gatepass_edit'),
    path('<int:pk>/checkin/', views.SecurityCheckInView.as_view(), name='gatepass_checkin'),
    path('<int:pk>/checkout/', views.SecurityCheckOutView.as_view(), name='gatepass_checkout'),
    path('<int:pk>/print/', views.PrintGatePassView.as_view(), name='gatepass_print'),
    
    # Visitor Log URLs
    path('visitors/', views.VisitorLogView.as_view(), name='visitor_log'),
    path('visitors/checkin/', views.VisitorCheckInView.as_view(), name='visitor_checkin'),
    path('visitors/<int:pk>/checkout/', views.VisitorCheckOutView.as_view(), name='visitor_checkout'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='security_dashboard'),
    
    # API Endpoints
    path('api/gatepass/<int:pk>/status/', views.UpdateGatePassStatus.as_view(), name='gatepass_status_api'),
]
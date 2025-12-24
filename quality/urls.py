from django.urls import path
from . import views

app_name = 'quality'

urlpatterns = [
    # Quality Check URLs
    path('checks/', views.QualityCheckListView.as_view(), name='qc_list'),
    path('checks/create/', views.QualityCheckCreateView.as_view(), name='qc_create'),
    path('checks/<int:pk>/', views.QualityCheckDetailView.as_view(), name='qc_detail'),
    path('checks/<int:pk>/update/', views.QualityCheckUpdateView.as_view(), name='qc_update'),
    path('checks/<int:pk>/delete/', views.QualityCheckDeleteView.as_view(), name='qc_delete'),
    path('checks/<int:pk>/perform/', views.perform_quality_check, name='qc_perform'),
    
    # NCR URLs
    path('ncr/', views.NCRListView.as_view(), name='ncr_list'),
    path('ncr/create/', views.NCRCreateView.as_view(), name='ncr_create'),
    path('ncr/<int:pk>/', views.NCRDetailView.as_view(), name='ncr_detail'),
    path('ncr/<int:pk>/update/', views.NCRUpdateView.as_view(), name='ncr_update'),
    path('ncr/<int:pk>/close/', views.close_ncr, name='ncr_close'),
    
    # Quality Parameter URLs
    path('parameters/', views.QualityParameterListView.as_view(), name='parameter_list'),
    path('parameters/create/', views.QualityParameterCreateView.as_view(), name='parameter_create'),
    
    # Quality Dashboard
    path('dashboard/', views.quality_dashboard, name='dashboard'),
    
    # Reports
    path('reports/defect-analysis/', views.defect_analysis_report, name='defect_analysis'),
    path('reports/quality-trends/', views.quality_trends_report, name='quality_trends'),
]
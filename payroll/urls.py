from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.PayrollDashboardView.as_view(), name='dashboard'),
    
    # Payroll Components
    path('components/', views.PayrollComponentListView.as_view(), name='component_list'),
    path('components/create/', views.PayrollComponentCreateView.as_view(), name='component_create'),
    path('components/<int:pk>/update/', views.PayrollComponentUpdateView.as_view(), name='component_update'),
    
    # Salary Structures
    path('salary-structures/', views.SalaryStructureListView.as_view(), name='salary_structure_list'),
    path('salary-structures/create/', views.SalaryStructureCreateView.as_view(), name='salary_structure_create'),
    path('salary-structures/<int:pk>/', views.SalaryStructureDetailView.as_view(), name='salary_structure_detail'),
    path('salary-structures/<int:pk>/update/', views.SalaryStructureUpdateView.as_view(), name='salary_structure_update'),
    
    # Payroll Periods
    path('periods/', views.PayrollPeriodListView.as_view(), name='period_list'),
    path('periods/create/', views.PayrollPeriodCreateView.as_view(), name='period_create'),
    
    # Payroll
    path('payrolls/', views.PayrollListView.as_view(), name='payroll_list'),
    path('payrolls/create/', views.PayrollCreateView.as_view(), name='payroll_create'),
    path('payrolls/<int:pk>/', views.PayrollDetailView.as_view(), name='payroll_detail'),
    path('payrolls/<int:pk>/approve/', views.ApprovePayrollView.as_view(), name='approve_payroll'),
    path('payrolls/<int:pk>/process/', views.ProcessPaymentView.as_view(), name='process_payment'),
    path('payrolls/<int:pk>/payslip/', views.GeneratePayslipView.as_view(), name='generate_payslip'),
    
    # Payroll Runs (Batch Processing)
    path('runs/', views.PayrollRunListView.as_view(), name='payroll_run_list'),
    path('runs/create/', views.PayrollRunCreateView.as_view(), name='payroll_run_create'),
    path('runs/<int:pk>/', views.PayrollRunDetailView.as_view(), name='payroll_run_detail'),
    
    # Loans
    path('loans/', views.LoanListView.as_view(), name='loan_list'),
    path('loans/create/', views.LoanCreateView.as_view(), name='loan_create'),
    path('loans/<int:pk>/', views.LoanDetailView.as_view(), name='loan_detail'),
    
    # Salary Advances
    path('advances/', views.SalaryAdvanceListView.as_view(), name='advance_list'),
    path('advances/create/', views.SalaryAdvanceCreateView.as_view(), name='advance_create'),
    path('advances/<int:pk>/', views.SalaryAdvanceDetailView.as_view(), name='advance_detail'),
    
    # AJAX Endpoints
    path('api/employee/<int:employee_id>/salary-structure/', 
         views.GetEmployeeSalaryStructureView.as_view(), name='get_employee_salary_structure'),
    path('api/summary/', views.GetPayrollSummaryView.as_view(), name='payroll_summary'),
]
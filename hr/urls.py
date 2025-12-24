from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    # Employee URLs
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employees/create/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/<int:pk>/update/', views.EmployeeUpdateView.as_view(), name='employee_update'),
    path('employees/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee_delete'),
    
    # Attendance URLs
    path('attendance/', views.AttendanceListView.as_view(), name='attendance_list'),
    path('attendance/today/', views.today_attendance, name='today_attendance'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/bulk-upload/', views.bulk_upload_attendance, name='bulk_upload_attendance'),
    
    # Leave URLs
    path('leaves/', views.LeaveApplicationListView.as_view(), name='leave_list'),
    path('leaves/create/', views.LeaveApplicationCreateView.as_view(), name='leave_create'),
    path('leaves/<int:pk>/', views.LeaveApplicationDetailView.as_view(), name='leave_detail'),
    path('leaves/<int:pk>/approve/', views.approve_leave, name='leave_approve'),
    path('leaves/<int:pk>/reject/', views.reject_leave, name='leave_reject'),
    
    # Shift URLs
    path('shifts/', views.ShiftListView.as_view(), name='shift_list'),
    path('shifts/create/', views.ShiftCreateView.as_view(), name='shift_create'),
    
    # Leave Type URLs
    path('leave-types/', views.LeaveTypeListView.as_view(), name='leavetype_list'),
    path('leave-types/create/', views.LeaveTypeCreateView.as_view(), name='leavetype_create'),
    
    # HR Dashboard
    path('dashboard/', views.hr_dashboard, name='dashboard'),
    
    # Reports
    path('reports/attendance/', views.attendance_report, name='attendance_report'),
    path('reports/leave-balance/', views.leave_balance_report, name='leave_balance_report'),
]
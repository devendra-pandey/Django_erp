from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse
from .models import Employee, Attendance, LeaveApplication, Shift, LeaveType, EmployeeShift
from .forms import EmployeeForm, AttendanceForm, LeaveApplicationForm, ShiftForm, LeaveTypeForm, EmployeeShiftForm

class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'hr/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Employee.objects.select_related('user', 'department').all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(employment_status=status)
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        return queryset.order_by('-created_at')

class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee_form.html'
    success_url = reverse_lazy('hr:employee_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Employee created successfully!')
        return super().form_valid(form)

class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = 'hr/employee_detail.html'
    context_object_name = 'employee'

class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee_form.html'
    success_url = reverse_lazy('hr:employee_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Employee updated successfully!')
        return super().form_valid(form)

class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = 'hr/employee_confirm_delete.html'
    success_url = reverse_lazy('hr:employee_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Employee deleted successfully!')
        return super().delete(request, *args, **kwargs)

class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'hr/attendance_list.html'
    context_object_name = 'attendances'
    
    def get_queryset(self):
        queryset = Attendance.objects.select_related('employee').all()
        date = self.request.GET.get('date')
        if date:
            queryset = queryset.filter(date=date)
        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        return queryset.order_by('-date')

def today_attendance(request):
    """Today's attendance view"""
    today = timezone.now().date()
    attendances = Attendance.objects.filter(date=today).select_related('employee')
    
    # Get all employees to show who hasn't been marked
    all_employees = Employee.objects.filter(employment_status='active')
    marked_employees = [att.employee for att in attendances]
    unmarked_employees = [emp for emp in all_employees if emp not in marked_employees]
    
    # Summary
    present = attendances.filter(status='present').count()
    absent = attendances.filter(status='absent').count()
    late = attendances.filter(status='present', check_in__gt='09:00').count()
    
    context = {
        'attendances': attendances,
        'unmarked_employees': unmarked_employees,
        'today': today,
        'present': present,
        'absent': absent,
        'late': late,
    }
    
    return render(request, 'hr/today_attendance.html', context)

def mark_attendance(request):
    """Mark attendance for employees"""
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        status = request.POST.get('status')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        
        employee = get_object_or_404(Employee, employee_id=employee_id)
        today = timezone.now().date()
        
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={
                'status': status,
                'check_in': check_in if check_in else None,
                'check_out': check_out if check_out else None
            }
        )
        
        if not created:
            attendance.status = status
            if check_in:
                attendance.check_in = check_in
            if check_out:
                attendance.check_out = check_out
            attendance.save()
        
        messages.success(request, f'Attendance marked for {employee.user.get_full_name()}')
        return redirect('hr:today_attendance')
    
    return render(request, 'hr/mark_attendance.html')

def bulk_upload_attendance(request):
    """Bulk upload attendance (simplified)"""
    if request.method == 'POST':
        # Simplified version - you can implement CSV upload here
        messages.info(request, 'Bulk upload feature coming soon!')
        return redirect('hr:attendance_list')
    
    return render(request, 'hr/bulk_upload_attendance.html')

class LeaveApplicationListView(LoginRequiredMixin, ListView):
    model = LeaveApplication
    template_name = 'hr/leave_list.html'
    context_object_name = 'leaves'
    
    def get_queryset(self):
        queryset = LeaveApplication.objects.select_related('employee', 'leave_type').all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')

class LeaveApplicationCreateView(LoginRequiredMixin, CreateView):
    model = LeaveApplication
    form_class = LeaveApplicationForm
    template_name = 'hr/leave_form.html'
    success_url = reverse_lazy('hr:leave_list')
    
    def form_valid(self, form):
        # Automatically set the employee to the current user's employee profile
        try:
            employee = self.request.user.employee
            form.instance.employee = employee
        except Employee.DoesNotExist:
            messages.error(self.request, 'You need an employee profile to apply for leave')
            return self.form_invalid(form)
        
        messages.success(self.request, 'Leave application submitted successfully!')
        return super().form_valid(form)

class LeaveApplicationDetailView(LoginRequiredMixin, DetailView):
    model = LeaveApplication
    template_name = 'hr/leave_detail.html'
    context_object_name = 'leave'

def approve_leave(request, pk):
    """Approve a leave application"""
    leave = get_object_or_404(LeaveApplication, pk=pk)
    if leave.status == 'pending':
        leave.status = 'approved'
        leave.approved_by = request.user
        leave.approved_date = timezone.now()
        leave.save()
        messages.success(request, f'Leave application {leave.application_number} approved!')
    else:
        messages.error(request, 'Only pending leaves can be approved.')
    return redirect('hr:leave_detail', pk=leave.pk)

def reject_leave(request, pk):
    """Reject a leave application"""
    leave = get_object_or_404(LeaveApplication, pk=pk)
    if leave.status == 'pending':
        leave.status = 'rejected'
        leave.approved_by = request.user
        leave.approved_date = timezone.now()
        leave.save()
        messages.success(request, f'Leave application {leave.application_number} rejected!')
    else:
        messages.error(request, 'Only pending leaves can be rejected.')
    return redirect('hr:leave_detail', pk=leave.pk)

class ShiftListView(LoginRequiredMixin, ListView):
    model = Shift
    template_name = 'hr/shift_list.html'
    context_object_name = 'shifts'

class ShiftCreateView(LoginRequiredMixin, CreateView):
    model = Shift
    form_class = ShiftForm
    template_name = 'hr/shift_form.html'
    success_url = reverse_lazy('hr:shift_list')

class LeaveTypeListView(LoginRequiredMixin, ListView):
    model = LeaveType
    template_name = 'hr/leavetype_list.html'
    context_object_name = 'leavetypes'

class LeaveTypeCreateView(LoginRequiredMixin, CreateView):
    model = LeaveType
    form_class = LeaveTypeForm
    template_name = 'hr/leavetype_form.html'
    success_url = reverse_lazy('hr:leavetype_list')

def hr_dashboard(request):
    """HR dashboard view"""
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(employment_status='active').count()
    on_leave = Employee.objects.filter(employment_status='on_leave').count()
    
    today = timezone.now().date()
    today_attendance_summary = Attendance.objects.filter(date=today).aggregate(
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
        late=Count('id', filter=Q(status='present', check_in__gt='09:00'))
    )
    
    pending_leaves = LeaveApplication.objects.filter(status='pending').count()
    
    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'on_leave': on_leave,
        'today_attendance': today_attendance_summary,
        'pending_leaves': pending_leaves,
    }
    
    return render(request, 'hr/dashboard.html', context)

def attendance_report(request):
    """Attendance report view"""
    # Simplified version
    return render(request, 'hr/reports/attendance.html')

def leave_balance_report(request):
    """Leave balance report view"""
    # Simplified version
    return render(request, 'hr/reports/leave_balance.html')
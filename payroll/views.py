from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from django.views import View  # Add this import
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.template.loader import get_template
from datetime import datetime, date, timedelta
import json
from decimal import Decimal

from .models import (
    PayrollComponent, EmployeeSalaryStructure, SalaryComponentValue,
    PayrollPeriod, Payroll, PayrollRun, PayrollItem, Loan, 
    SalaryAdvance, Payslip
)
from .forms import (
    PayrollComponentForm, EmployeeSalaryStructureForm, SalaryComponentValueFormSet,
    PayrollPeriodForm, PayrollForm, PayrollRunForm, LoanForm, SalaryAdvanceForm
)
from hr.models import Employee, Department, Attendance
from core.models import Company

class PayrollDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'payroll/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics
        today = timezone.now().date()
        current_month = today.replace(day=1)
        
        context['total_employees'] = Employee.objects.filter(employment_status='active').count()
        context['total_payrolls'] = Payroll.objects.count()
        context['pending_payrolls'] = Payroll.objects.filter(status='draft').count()
        context['paid_this_month'] = Payroll.objects.filter(
            payment_date__month=today.month,
            payment_date__year=today.year,
            status='paid'
        ).count()
        
        # Recent payrolls
        context['recent_payrolls'] = Payroll.objects.select_related('employee', 'payroll_period').order_by('-created_at')[:10]
        
        # Upcoming payroll periods
        context['upcoming_periods'] = PayrollPeriod.objects.filter(
            start_date__gte=today,
            is_processed=False
        ).order_by('start_date')[:5]
        
        # Department-wise summary
        context['department_summary'] = Department.objects.annotate(
            employee_count=Count('employee', filter=Q(employee__employment_status='active')),
            payroll_count=Count('employee__payrolls', filter=Q(employee__payrolls__status='paid'))
        )
        
        return context

class PayrollComponentListView(LoginRequiredMixin, ListView):
    model = PayrollComponent
    template_name = 'payroll/component_list.html'
    context_object_name = 'components'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PayrollComponent.objects.all()
        component_type = self.request.GET.get('type')
        if component_type:
            queryset = queryset.filter(component_type=component_type)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )
        active = self.request.GET.get('active')
        if active == 'true':
            queryset = queryset.filter(is_active=True)
        elif active == 'false':
            queryset = queryset.filter(is_active=False)
        return queryset.order_by('component_type', 'priority')

class PayrollComponentCreateView(LoginRequiredMixin, CreateView):
    model = PayrollComponent
    form_class = PayrollComponentForm
    template_name = 'payroll/component_form.html'
    success_url = reverse_lazy('payroll:component_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Payroll component created successfully!')
        return super().form_valid(form)

class PayrollComponentUpdateView(LoginRequiredMixin, UpdateView):
    model = PayrollComponent
    form_class = PayrollComponentForm
    template_name = 'payroll/component_form.html'
    success_url = reverse_lazy('payroll:component_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Payroll component updated successfully!')
        return super().form_valid(form)

class SalaryStructureListView(LoginRequiredMixin, ListView):
    model = EmployeeSalaryStructure
    template_name = 'payroll/salary_structure_list.html'
    context_object_name = 'structures'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = EmployeeSalaryStructure.objects.select_related('employee').all()
        department_id = self.request.GET.get('department')
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        active = self.request.GET.get('active')
        if active == 'true':
            queryset = queryset.filter(is_active=True)
        elif active == 'false':
            queryset = queryset.filter(is_active=False)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(employee__user__first_name__icontains=search) |
                Q(employee__user__last_name__icontains=search) |
                Q(employee__employee_id__icontains=search)
            )
        return queryset.order_by('-effective_from')

class SalaryStructureCreateView(LoginRequiredMixin, CreateView):
    model = EmployeeSalaryStructure
    form_class = EmployeeSalaryStructureForm
    template_name = 'payroll/salary_structure_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = SalaryComponentValueFormSet(self.request.POST)
        else:
            context['formset'] = SalaryComponentValueFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save(commit=False)
            self.object.created_by = self.request.user
            self.object.save()
            
            formset.instance = self.object
            formset.save()
            
            messages.success(self.request, 'Salary structure created successfully!')
            return redirect('payroll:salary_structure_detail', pk=self.object.pk)
        
        return self.form_invalid(form)

class SalaryStructureDetailView(LoginRequiredMixin, DetailView):
    model = EmployeeSalaryStructure
    template_name = 'payroll/salary_structure_detail.html'
    context_object_name = 'structure'

class SalaryStructureUpdateView(LoginRequiredMixin, UpdateView):
    model = EmployeeSalaryStructure
    form_class = EmployeeSalaryStructureForm
    template_name = 'payroll/salary_structure_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = SalaryComponentValueFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = SalaryComponentValueFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save(commit=False)
            self.object.updated_by = self.request.user
            self.object.save()
            
            formset.instance = self.object
            formset.save()
            
            messages.success(self.request, 'Salary structure updated successfully!')
            return redirect('payroll:salary_structure_detail', pk=self.object.pk)
        
        return self.form_invalid(form)

class PayrollPeriodListView(LoginRequiredMixin, ListView):
    model = PayrollPeriod
    template_name = 'payroll/period_list.html'
    context_object_name = 'periods'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PayrollPeriod.objects.all()
        processed = self.request.GET.get('processed')
        if processed == 'true':
            queryset = queryset.filter(is_processed=True)
        elif processed == 'false':
            queryset = queryset.filter(is_processed=False)
        year = self.request.GET.get('year')
        if year:
            queryset = queryset.filter(start_date__year=year)
        return queryset.order_by('-start_date')

class PayrollPeriodCreateView(LoginRequiredMixin, CreateView):
    model = PayrollPeriod
    form_class = PayrollPeriodForm
    template_name = 'payroll/period_form.html'
    success_url = reverse_lazy('payroll:period_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Payroll period created successfully!')
        return super().form_valid(form)

class PayrollListView(LoginRequiredMixin, ListView):
    model = Payroll
    template_name = 'payroll/payroll_list.html'
    context_object_name = 'payrolls'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Payroll.objects.select_related('employee', 'payroll_period').all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        period_id = self.request.GET.get('period')
        if period_id:
            queryset = queryset.filter(payroll_period_id=period_id)
        department_id = self.request.GET.get('department')
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(payroll_number__icontains=search) |
                Q(employee__user__first_name__icontains=search) |
                Q(employee__user__last_name__icontains=search) |
                Q(employee__employee_id__icontains=search)
            )
        return queryset.order_by('-payroll_period__start_date', 'employee__employee_id')

class PayrollCreateView(LoginRequiredMixin, CreateView):
    model = Payroll
    form_class = PayrollForm
    template_name = 'payroll/payroll_form.html'
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        
        # Calculate attendance
        self.calculate_attendance()
        
        # Calculate salary based on structure
        self.calculate_salary()
        
        self.object.save()
        
        messages.success(self.request, f'Payroll {self.object.payroll_number} created successfully!')
        return redirect('payroll:payroll_detail', pk=self.object.pk)
    
    def calculate_attendance(self):
        """Calculate attendance for the payroll period"""
        period = self.object.payroll_period
        employee = self.object.employee
        
        # Get attendance records for the period
        attendance_records = Attendance.objects.filter(
            employee=employee,
            date__range=[period.start_date, period.end_date]
        )
        
        # Count days
        self.object.total_working_days = (period.end_date - period.start_date).days + 1
        self.object.present_days = attendance_records.filter(status='present').count()
        self.object.absent_days = attendance_records.filter(status='absent').count()
        self.object.leave_days = attendance_records.filter(status='leave').count()
        self.object.holiday_days = attendance_records.filter(status='holiday').count()
        
        # Calculate overtime
        overtime_hours = attendance_records.aggregate(
            total_overtime=Sum('overtime_hours')
        )['total_overtime'] or 0
        # Assuming overtime rate is 1.5x hourly rate
        hourly_rate = self.object.salary_structure.basic_salary / (22 * 8)  # 22 working days, 8 hours/day
        self.object.overtime_amount = Decimal(str(overtime_hours)) * hourly_rate * Decimal('1.5')
    
    def calculate_salary(self):
        """Calculate salary based on structure and attendance"""
        structure = self.object.salary_structure
        
        # Basic salary (prorated based on attendance)
        daily_rate = structure.basic_salary / self.object.total_working_days
        payable_days = self.object.present_days + self.object.holiday_days + (self.object.leave_days * 0.5)  # Half pay for leaves
        
        self.object.basic_salary = daily_rate * payable_days
        
        # Calculate other components from salary structure
        for component_value in structure.components.all():
            component = component_value.component
            
            if component.component_type == 'earning':
                if component.calculation_type == 'fixed':
                    amount = component_value.amount
                elif component.calculation_type == 'percentage':
                    amount = self.object.basic_salary * (component_value.percentage / 100)
                else:
                    amount = component_value.amount  # Default
                
                # Map to appropriate field based on component code
                if component.code == 'HRA':
                    self.object.house_rent_allowance = amount
                elif component.code == 'CA':
                    self.object.conveyance_allowance = amount
                elif component.code == 'MA':
                    self.object.medical_allowance = amount
                elif component.code == 'SA':
                    self.object.special_allowance = amount
                else:
                    self.object.other_earnings += amount
                
                # Create payroll item
                PayrollItem.objects.create(
                    payroll=self.object,
                    component=component,
                    amount=amount,
                    calculation_note=f"{component.calculation_type} calculation"
                )
            
            elif component.component_type == 'deduction':
                if component.calculation_type == 'fixed':
                    amount = component_value.amount
                elif component.calculation_type == 'percentage':
                    amount = self.object.basic_salary * (component_value.percentage / 100)
                else:
                    amount = component_value.amount
                
                # Map to appropriate field
                if component.code == 'PF':
                    self.object.provident_fund = amount
                elif component.code == 'PT':
                    self.object.professional_tax = amount
                elif component.code == 'IT':
                    self.object.income_tax = amount
                else:
                    self.object.other_deductions += amount
                
                # Create payroll item
                PayrollItem.objects.create(
                    payroll=self.object,
                    component=component,
                    amount=amount,
                    calculation_note=f"{component.calculation_type} calculation"
                )
        
        # Calculate loan deductions
        active_loans = Loan.objects.filter(
            employee=self.object.employee,
            status='active'
        )
        for loan in active_loans:
            installment = loan.installments.filter(
                due_date__range=[self.object.payroll_period.start_date, self.object.payroll_period.end_date],
                status__in=['pending', 'due']
            ).first()
            
            if installment:
                self.object.loan_deduction += installment.total_amount
                PayrollItem.objects.create(
                    payroll=self.object,
                    component=PayrollComponent.objects.get_or_create(
                        code=f'LOAN-{loan.loan_number}',
                        defaults={
                            'name': f'Loan Deduction - {loan.loan_number}',
                            'component_type': 'deduction',
                            'calculation_type': 'fixed',
                            'is_taxable': False
                        }
                    )[0],
                    amount=installment.total_amount,
                    calculation_note=f"Loan installment #{installment.installment_number}"
                )
        
        # Calculate advance deductions
        active_advances = SalaryAdvance.objects.filter(
            employee=self.object.employee,
            status='disbursed',
            remaining_amount__gt=0
        )
        for advance in active_advances:
            deduction_amount = min(advance.monthly_deduction, advance.remaining_amount)
            self.object.advance_deduction += deduction_amount
            advance.remaining_amount -= deduction_amount
            if advance.remaining_amount <= 0:
                advance.status = 'repaid'
            advance.save()
            
            PayrollItem.objects.create(
                payroll=self.object,
                component=PayrollComponent.objects.get_or_create(
                    code=f'ADV-{advance.advance_number}',
                    defaults={
                        'name': f'Advance Deduction - {advance.advance_number}',
                        'component_type': 'deduction',
                        'calculation_type': 'fixed',
                        'is_taxable': False
                    }
                )[0],
                amount=deduction_amount,
                calculation_note=f"Salary advance repayment"
            )
        
        # Recalculate totals
        self.object.calculate_totals()

class PayrollDetailView(LoginRequiredMixin, DetailView):
    model = Payroll
    template_name = 'payroll/payroll_detail.html'
    context_object_name = 'payroll'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('component').all()
        return context

class PayrollRunCreateView(LoginRequiredMixin, CreateView):
    model = PayrollRun
    form_class = PayrollRunForm
    template_name = 'payroll/payroll_run_form.html'
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.started_by = self.request.user
        self.object.status = 'pending'
        self.object.save()
        
        # Start batch processing in background (you might want to use Celery for this)
        self.process_payroll_run()
        
        messages.success(self.request, f'Payroll run {self.object.run_number} started successfully!')
        return redirect('payroll:payroll_run_detail', pk=self.object.pk)
    
    def process_payroll_run(self):
        """Process payroll for multiple employees based on run type"""
        from django.db import transaction
        
        try:
            self.object.status = 'processing'
            self.object.save()
            
            # Get employees based on run type
            if self.object.run_type == 'department' and self.object.department:
                employees = Employee.objects.filter(
                    department=self.object.department,
                    employment_status='active',
                    salary_structure__is_active=True
                )
            elif self.object.run_type == 'all':
                employees = Employee.objects.filter(
                    employment_status='active',
                    salary_structure__is_active=True
                )
            else:
                # Handle other run types (company, branch, custom)
                employees = Employee.objects.filter(
                    employment_status='active',
                    salary_structure__is_active=True
                )
            
            self.object.total_employees = employees.count()
            self.object.save()
            
            processed_count = 0
            failed_count = 0
            total_amount = Decimal('0')
            
            for employee in employees:
                try:
                    with transaction.atomic():
                        # Check if payroll already exists for this period
                        existing_payroll = Payroll.objects.filter(
                            employee=employee,
                            payroll_period=self.object.payroll_period
                        ).exists()
                        
                        if not existing_payroll:
                            # Create payroll
                            payroll = Payroll(
                                employee=employee,
                                payroll_period=self.object.payroll_period,
                                salary_structure=employee.salary_structure,
                                created_by=self.request.user
                            )
                            
                            # Calculate attendance
                            self.calculate_attendance_for_payroll(payroll)
                            
                            # Calculate salary
                            self.calculate_salary_for_payroll(payroll)
                            
                            payroll.save()
                            
                            # Generate payslip
                            self.generate_payslip(payroll)
                            
                            total_amount += payroll.net_salary
                            processed_count += 1
                        else:
                            failed_count += 1
                            self.object.error_log += f"\nPayroll already exists for {employee.employee_id}"
                
                except Exception as e:
                    failed_count += 1
                    self.object.error_log += f"\nError processing {employee.employee_id}: {str(e)}"
                    continue
            
            # Update run results
            self.object.processed_employees = processed_count
            self.object.failed_employees = failed_count
            self.object.total_amount = total_amount
            self.object.status = 'completed'
            self.object.completed_by = self.request.user
            self.object.completed_at = timezone.now()
            self.object.save()
            
            # Mark payroll period as processed
            self.object.payroll_period.is_processed = True
            self.object.payroll_period.processed_by = self.request.user
            self.object.payroll_period.processed_date = timezone.now()
            self.object.payroll_period.save()
            
        except Exception as e:
            self.object.status = 'failed'
            self.object.error_log += f"\nRun failed: {str(e)}"
            self.object.save()
    
    def calculate_attendance_for_payroll(self, payroll):
        """Calculate attendance for a payroll"""
        # Similar to calculate_attendance method in PayrollCreateView
        pass
    
    def calculate_salary_for_payroll(self, payroll):
        """Calculate salary for a payroll"""
        # Similar to calculate_salary method in PayrollCreateView
        pass
    
    def generate_payslip(self, payroll):
        """Generate payslip for payroll"""
        Payslip.objects.create(
            payroll=payroll,
            generated_by=self.request.user
        )

class PayrollRunListView(LoginRequiredMixin, ListView):
    """List all payroll runs"""
    model = PayrollRun
    template_name = 'payroll/payroll_run_list.html'
    context_object_name = 'payroll_runs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PayrollRun.objects.select_related('payroll_period', 'department', 'started_by').all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by run type
        run_type = self.request.GET.get('run_type')
        if run_type:
            queryset = queryset.filter(run_type=run_type)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(started_at__date__range=[start_date, end_date])
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(run_number__icontains=search) |
                Q(started_by__username__icontains=search) |
                Q(department__name__icontains=search)
            )
        
        return queryset.order_by('-started_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter choices to context
        context['run_types'] = PayrollRun.RUN_TYPES
        context['status_choices'] = [
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ]
        
        # Statistics
        context['total_runs'] = PayrollRun.objects.count()
        context['completed_runs'] = PayrollRun.objects.filter(status='completed').count()
        context['pending_runs'] = PayrollRun.objects.filter(status='pending').count()
        context['failed_runs'] = PayrollRun.objects.filter(status='failed').count()
        
        return context


class PayrollRunDetailView(LoginRequiredMixin, DetailView):
    model = PayrollRun
    template_name = 'payroll/payroll_run_detail.html'
    context_object_name = 'payroll_run'

class GeneratePayslipView(LoginRequiredMixin, View):
    """Generate PDF payslip"""
    
    def get(self, request, pk):
        payroll = get_object_or_404(Payroll, pk=pk)
        
        # Get or create payslip
        payslip, created = Payslip.objects.get_or_create(
            payroll=payroll,
            defaults={'generated_by': request.user}
        )
        
        # Generate PDF (you'll need to install reportlab or use xhtml2pdf)
        # This is a simplified example
        
        from io import BytesIO
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add content to PDF
        p.drawString(100, 750, f"PAYSLIP - {payroll.payroll_number}")
        p.drawString(100, 730, f"Employee: {payroll.employee.user.get_full_name()}")
        p.drawString(100, 710, f"Employee ID: {payroll.employee.employee_id}")
        p.drawString(100, 690, f"Period: {payroll.payroll_period.name}")
        
        # Earnings
        p.drawString(100, 650, "EARNINGS")
        p.drawString(100, 630, f"Basic Salary: ${payroll.basic_salary}")
        p.drawString(100, 610, f"Allowances: ${payroll.total_earnings - payroll.basic_salary}")
        
        # Deductions
        p.drawString(100, 570, "DEDUCTIONS")
        p.drawString(100, 550, f"Total Deductions: ${payroll.total_deductions}")
        
        # Net Salary
        p.drawString(100, 500, f"NET SALARY: ${payroll.net_salary}")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        
        # Update payslip
        payslip.pdf_file.save(f'payslip_{payroll.payroll_number}.pdf', buffer)
        payslip.save()
        
        # Return PDF
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="payslip_{payroll.payroll_number}.pdf"'
        return response

class ApprovePayrollView(LoginRequiredMixin, View):
    """Approve payroll"""
    
    def post(self, request, pk):
        payroll = get_object_or_404(Payroll, pk=pk)
        
        if payroll.status == 'calculated':
            payroll.status = 'approved'
            payroll.approved_by = request.user
            payroll.approved_date = timezone.now()
            payroll.save()
            
            messages.success(request, f'Payroll {payroll.payroll_number} approved successfully!')
        else:
            messages.error(request, 'Only calculated payrolls can be approved.')
        
        return redirect('payroll:payroll_detail', pk=payroll.pk)

class ProcessPaymentView(LoginRequiredMixin, View):
    """Mark payroll as paid"""
    
    def post(self, request, pk):
        payroll = get_object_or_404(Payroll, pk=pk)
        
        if payroll.status == 'approved':
            payroll.status = 'paid'
            payroll.processed_by = request.user
            payroll.processed_date = timezone.now()
            if not payroll.payment_date:
                payroll.payment_date = date.today()
            payroll.save()
            
            messages.success(request, f'Payment processed for {payroll.payroll_number}!')
        else:
            messages.error(request, 'Only approved payrolls can be marked as paid.')
        
        return redirect('payroll:payroll_detail', pk=payroll.pk)

# Loan Views
class LoanListView(LoginRequiredMixin, ListView):
    model = Loan
    template_name = 'payroll/loan_list.html'
    context_object_name = 'loans'
    paginate_by = 20

class LoanCreateView(LoginRequiredMixin, CreateView):
    model = Loan
    form_class = LoanForm
    template_name = 'payroll/loan_form.html'
    success_url = reverse_lazy('payroll:loan_list')

class LoanDetailView(LoginRequiredMixin, DetailView):
    model = Loan
    template_name = 'payroll/loan_detail.html'
    context_object_name = 'loan'

# Salary Advance Views
class SalaryAdvanceListView(LoginRequiredMixin, ListView):
    model = SalaryAdvance
    template_name = 'payroll/advance_list.html'
    context_object_name = 'advances'
    paginate_by = 20

class SalaryAdvanceCreateView(LoginRequiredMixin, CreateView):
    model = SalaryAdvance
    form_class = SalaryAdvanceForm
    template_name = 'payroll/advance_form.html'
    success_url = reverse_lazy('payroll:advance_list')

class SalaryAdvanceDetailView(LoginRequiredMixin, DetailView):
    model = SalaryAdvance
    template_name = 'payroll/advance_detail.html'
    context_object_name = 'advance'

# AJAX Views
class GetEmployeeSalaryStructureView(LoginRequiredMixin, View):
    """Get employee salary structure for payroll"""
    
    def get(self, request, employee_id):
        try:
            employee = Employee.objects.get(pk=employee_id)
            structure = employee.salary_structure
            
            if structure and structure.is_active:
                data = {
                    'success': True,
                    'basic_salary': str(structure.basic_salary),
                    'components': [
                        {
                            'name': scv.component.name,
                            'code': scv.component.code,
                            'type': scv.component.component_type,
                            'calculation_type': scv.component.calculation_type,
                            'amount': str(scv.amount),
                            'percentage': str(scv.percentage)
                        }
                        for scv in structure.components.all()
                    ]
                }
            else:
                data = {'success': False, 'error': 'No active salary structure found'}
        
        except Employee.DoesNotExist:
            data = {'success': False, 'error': 'Employee not found'}
        
        return JsonResponse(data)

class GetPayrollSummaryView(LoginRequiredMixin, View):
    """Get payroll summary for dashboard"""
    
    def get(self, request):
        today = date.today()
        year = request.GET.get('year', today.year)
        
        # Monthly payroll summary
        monthly_data = []
        for month in range(1, 13):
            payrolls = Payroll.objects.filter(
                payroll_period__start_date__year=year,
                payroll_period__start_date__month=month,
                status='paid'
            )
            total_amount = payrolls.aggregate(total=Sum('net_salary'))['total'] or 0
            monthly_data.append({
                'month': datetime(year, month, 1).strftime('%b'),
                'amount': float(total_amount),
                'count': payrolls.count()
            })
        
        # Department summary
        department_summary = []
        for dept in Department.objects.all():
            payrolls = Payroll.objects.filter(
                employee__department=dept,
                payroll_period__start_date__year=year,
                status='paid'
            )
            if payrolls.exists():
                total = payrolls.aggregate(total=Sum('net_salary'))['total'] or 0
                department_summary.append({
                    'department': dept.name,
                    'amount': float(total),
                    'count': payrolls.count()
                })
        
        data = {
            'monthly_summary': monthly_data,
            'department_summary': department_summary,
            'total_paid': float(Payroll.objects.filter(status='paid').aggregate(total=Sum('net_salary'))['total'] or 0),
            'pending_payrolls': Payroll.objects.filter(status='draft').count()
        }
        
        return JsonResponse(data)
    


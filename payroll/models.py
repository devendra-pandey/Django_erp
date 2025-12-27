from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from core.models import TimeStampedModel
from hr.models import Employee, Department, Attendance
from datetime import datetime, date

class PayrollComponent(TimeStampedModel):
    """Salary components like Basic, DA, HRA, etc."""
    COMPONENT_TYPES = [
        ('earning', 'Earning'),
        ('deduction', 'Deduction'),
    ]
    
    CALCULATION_TYPES = [
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage of Basic'),
        ('formula', 'Formula Based'),
        ('attendance', 'Attendance Based'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPES, default='fixed')
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    percentage_of = models.CharField(max_length=50, blank=True, null=True)
    formula = models.TextField(blank=True, null=True)
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)  # For calculation order
    
    class Meta:
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.get_component_type_display()})"

class EmployeeSalaryStructure(TimeStampedModel):
    """Salary structure for each employee"""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary_structure')
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ctc = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Cost to Company
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.employee.employee_id} - Salary Structure"

class SalaryComponentValue(models.Model):
    """Component values for each salary structure"""
    salary_structure = models.ForeignKey(EmployeeSalaryStructure, on_delete=models.CASCADE, related_name='components')
    component = models.ForeignKey(PayrollComponent, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    formula = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['salary_structure', 'component']
    
    def __str__(self):
        return f"{self.salary_structure.employee.employee_id} - {self.component.name}"

class PayrollPeriod(models.Model):
    """Payroll period for salary processing"""
    PERIOD_TYPES = [
        ('monthly', 'Monthly'),
        ('biweekly', 'Bi-Weekly'),
        ('weekly', 'Weekly'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=100)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, default='monthly')
    start_date = models.DateField()
    end_date = models.DateField()
    payment_date = models.DateField()
    is_locked = models.BooleanField(default=False)
    is_processed = models.BooleanField(default=False)
    processed_date = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ['start_date', 'end_date']
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"
    
    @property
    def month_year(self):
        return self.start_date.strftime('%B %Y')

class Payroll(TimeStampedModel):
    """Main payroll record"""
    PAYROLL_STATUS = [
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('approved', 'Approved'),
        ('processed', 'Processed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('cash', 'Cash'),
        ('online', 'Online Payment'),
    ]
    
    payroll_number = models.CharField(max_length=50, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='payrolls')
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.PROTECT)
    salary_structure = models.ForeignKey(EmployeeSalaryStructure, on_delete=models.PROTECT)
    
    # Attendance Details
    total_working_days = models.IntegerField(default=0)
    present_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    leave_days = models.IntegerField(default=0)
    holiday_days = models.IntegerField(default=0)
    
    # Earnings
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    house_rent_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    conveyance_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Deductions
    provident_fund = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    professional_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    income_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    loan_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Final Amounts
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Status and Payment
    status = models.CharField(max_length=20, choices=PAYROLL_STATUS, default='draft')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='bank_transfer')
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Approvals
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payrolls')
    approved_date = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payrolls')
    processed_date = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.payroll_number:
            year = timezone.now().year
            month = timezone.now().month
            last_payroll = Payroll.objects.filter(
                payroll_number__startswith=f"PR-{year}-{month:02d}"
            ).order_by('id').last()
            
            if last_payroll:
                last_number = int(last_payroll.payroll_number.split('-')[-1])
                self.payroll_number = f"PR-{year}-{month:02d}-{last_number + 1:05d}"
            else:
                self.payroll_number = f"PR-{year}-{month:02d}-00001"
        
        # Auto-calculate totals
        self.calculate_totals()
        
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate all totals automatically"""
        # Calculate total earnings
        earnings = [
            self.basic_salary,
            self.house_rent_allowance,
            self.conveyance_allowance,
            self.medical_allowance,
            self.special_allowance,
            self.overtime_amount,
            self.bonus,
            self.other_earnings
        ]
        self.total_earnings = sum(earnings)
        
        # Calculate total deductions
        deductions = [
            self.provident_fund,
            self.professional_tax,
            self.income_tax,
            self.loan_deduction,
            self.advance_deduction,
            self.other_deductions
        ]
        self.total_deductions = sum(deductions)
        
        # Calculate gross and net salary
        self.gross_salary = self.total_earnings
        self.net_salary = self.total_earnings - self.total_deductions
    
    def __str__(self):
        return f"{self.payroll_number} - {self.employee.employee_id}"

class PayrollItem(models.Model):
    """Detailed breakdown of payroll components"""
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='items')
    component = models.ForeignKey(PayrollComponent, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    calculation_note = models.TextField(blank=True)
    
    class Meta:
        ordering = ['component__priority']
    
    def __str__(self):
        return f"{self.payroll.payroll_number} - {self.component.name}"

class PayrollRun(TimeStampedModel):
    """Batch payroll processing"""
    RUN_TYPES = [
        ('department', 'By Department'),
        ('company', 'By Company'),
        ('branch', 'By Branch'),
        ('custom', 'Custom Selection'),
        ('all', 'All Employees'),
    ]
    
    run_number = models.CharField(max_length=50, unique=True)
    run_type = models.CharField(max_length=20, choices=RUN_TYPES)
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.PROTECT)
    
    # Filters for batch processing
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    # Add branch field if you have Branch model
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    
    # Results
    total_employees = models.IntegerField(default=0)
    processed_employees = models.IntegerField(default=0)
    failed_employees = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Audit
    started_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='payroll_runs_started')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payroll_runs_completed')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    error_log = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.run_number:
            year = timezone.now().year
            last_run = PayrollRun.objects.filter(
                run_number__startswith=f"RUN-{year}"
            ).order_by('id').last()
            
            if last_run:
                last_number = int(last_run.run_number.split('-')[-1])
                self.run_number = f"RUN-{year}-{last_number + 1:05d}"
            else:
                self.run_number = f"RUN-{year}-00001"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.run_number} - {self.get_run_type_display()}"

class Loan(models.Model):
    """Employee loans"""
    LOAN_TYPES = [
        ('personal', 'Personal Loan'),
        ('housing', 'Housing Loan'),
        ('vehicle', 'Vehicle Loan'),
        ('education', 'Education Loan'),
        ('medical', 'Medical Loan'),
        ('other', 'Other'),
    ]
    
    LOAN_STATUS = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    
    loan_number = models.CharField(max_length=50, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tenure_months = models.IntegerField()
    emi_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='pending')
    
    # Remaining
    principal_balance = models.DecimalField(max_digits=12, decimal_places=2)
    interest_balance = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Approvals
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.loan_number:
            year = timezone.now().year
            last_loan = Loan.objects.filter(
                loan_number__startswith=f"LN-{year}"
            ).order_by('id').last()
            
            if last_loan:
                last_number = int(last_loan.loan_number.split('-')[-1])
                self.loan_number = f"LN-{year}-{last_number + 1:05d}"
            else:
                self.loan_number = f"LN-{year}-00001"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.loan_number} - {self.employee.employee_id}"

class LoanInstallment(models.Model):
    """Loan installments for deduction"""
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='installments')
    installment_number = models.IntegerField()
    due_date = models.DateField()
    principal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('due', 'Due'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
    ], default='pending')
    paid_date = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['installment_number']
        unique_together = ['loan', 'installment_number']
    
    def __str__(self):
        return f"{self.loan.loan_number} - Installment {self.installment_number}"

class SalaryAdvance(models.Model):
    """Salary advance payments"""
    advance_number = models.CharField(max_length=50, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_advances')
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2)
    requested_date = models.DateField()
    approved_date = models.DateField(null=True, blank=True)
    repayment_months = models.IntegerField(default=1)
    monthly_deduction = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('repaid', 'Fully Repaid'),
    ], default='pending')
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.advance_number:
            year = timezone.now().year
            last_advance = SalaryAdvance.objects.filter(
                advance_number__startswith=f"ADV-{year}"
            ).order_by('id').last()
            
            if last_advance:
                last_number = int(last_advance.advance_number.split('-')[-1])
                self.advance_number = f"ADV-{year}-{last_number + 1:05d}"
            else:
                self.advance_number = f"ADV-{year}-00001"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.advance_number} - {self.employee.employee_id}"

class Payslip(models.Model):
    """Generated payslips for employees"""
    payroll = models.OneToOneField(Payroll, on_delete=models.CASCADE, related_name='payslip')
    generated_date = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    pdf_file = models.FileField(upload_to='payslips/%Y/%m/', null=True, blank=True)
    is_downloaded = models.BooleanField(default=False)
    downloaded_date = models.DateTimeField(null=True, blank=True)
    is_emailed = models.BooleanField(default=False)
    emailed_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payslip - {self.payroll.payroll_number}"
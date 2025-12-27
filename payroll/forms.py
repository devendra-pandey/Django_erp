from django import forms
from django.forms import inlineformset_factory
from .models import (
    PayrollComponent, EmployeeSalaryStructure, SalaryComponentValue,
    PayrollPeriod, Payroll, PayrollRun, Loan, SalaryAdvance
)
from hr.models import Employee, Department

class PayrollComponentForm(forms.ModelForm):
    class Meta:
        model = PayrollComponent
        fields = '__all__'
        widgets = {
            'formula': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

class EmployeeSalaryStructureForm(forms.ModelForm):
    class Meta:
        model = EmployeeSalaryStructure
        fields = ['employee', 'effective_from', 'effective_to', 'basic_salary', 'total_ctc', 'is_active', 'notes']
        widgets = {
            'effective_from': forms.DateInput(attrs={'type': 'date'}),
            'effective_to': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active employees
        self.fields['employee'].queryset = Employee.objects.filter(employment_status='active')

class SalaryComponentValueForm(forms.ModelForm):
    class Meta:
        model = SalaryComponentValue
        fields = ['component', 'amount', 'percentage', 'formula']

SalaryComponentValueFormSet = inlineformset_factory(
    EmployeeSalaryStructure,
    SalaryComponentValue,
    form=SalaryComponentValueForm,
    extra=5,
    can_delete=True
)

class PayrollPeriodForm(forms.ModelForm):
    class Meta:
        model = PayrollPeriod
        fields = ['name', 'period_type', 'start_date', 'end_date', 'payment_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        exclude = ['payroll_number', 'created_at', 'updated_at', 'created_by', 'updated_by']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active employees with salary structure
        self.fields['employee'].queryset = Employee.objects.filter(
            employment_status='active',
            salary_structure__is_active=True
        ).distinct()
        
        # Filter only unprocessed payroll periods
        self.fields['payroll_period'].queryset = PayrollPeriod.objects.filter(
            is_processed=False
        )

class PayrollRunForm(forms.ModelForm):
    class Meta:
        model = PayrollRun
        fields = ['run_type', 'payroll_period', 'department', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only unprocessed payroll periods
        self.fields['payroll_period'].queryset = PayrollPeriod.objects.filter(
            is_processed=False
        )

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['employee', 'loan_type', 'loan_amount', 'interest_rate', 
                  'tenure_months', 'start_date', 'end_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active employees
        self.fields['employee'].queryset = Employee.objects.filter(employment_status='active')

class SalaryAdvanceForm(forms.ModelForm):
    class Meta:
        model = SalaryAdvance
        fields = ['employee', 'advance_amount', 'repayment_months', 'notes']
        widgets = {
            'requested_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active employees
        self.fields['employee'].queryset = Employee.objects.filter(employment_status='active')
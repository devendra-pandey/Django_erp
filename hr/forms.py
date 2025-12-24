from django import forms
from django.contrib.auth.models import User
from .models import Employee, LeaveApplication, Attendance, Shift, LeaveType, EmployeeShift

class EmployeeForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(employee__isnull=True),
        required=True,
        help_text="Select a user who doesn't already have an employee profile"
    )
    
    class Meta:
        model = Employee
        fields = ['user', 'employee_id', 'department', 'designation', 'employee_type',
                 'employment_status', 'date_of_joining', 'date_of_birth', 'gender',
                 'phone', 'emergency_contact', 'emergency_contact_name', 'address',
                 'photo', 'bank_account', 'bank_name', 'basic_salary']
        widgets = {
            'date_of_joining': forms.DateInput(attrs={'type': 'date'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['photo']:
                if not isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-control'

class LeaveApplicationForm(forms.ModelForm):
    class Meta:
        model = LeaveApplication
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'check_in', 'check_out', 'status', 
                 'overtime_hours', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'check_in': forms.TimeInput(attrs={'type': 'time'}),
            'check_out': forms.TimeInput(attrs={'type': 'time'}),
            'overtime_hours': forms.NumberInput(attrs={'step': '0.25'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'

class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['name', 'code', 'start_time', 'end_time', 
                 'break_start', 'break_end', 'is_active']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'break_start': forms.TimeInput(attrs={'type': 'time'}),
            'break_end': forms.TimeInput(attrs={'type': 'time'}),
        }

class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        fields = ['name', 'code', 'days_per_year', 'carry_forward', 
                 'max_carry_forward', 'requires_approval', 'is_active']

class EmployeeShiftForm(forms.ModelForm):
    class Meta:
        model = EmployeeShift
        fields = ['employee', 'shift', 'effective_from', 'effective_to', 'is_active']
        widgets = {
            'effective_from': forms.DateInput(attrs={'type': 'date'}),
            'effective_to': forms.DateInput(attrs={'type': 'date'}),
        }
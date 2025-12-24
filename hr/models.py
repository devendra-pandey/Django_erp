from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel, Department
from django.utils import timezone

class Employee(TimeStampedModel):
    EMPLOYEE_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ]
    
    EMPLOYEE_TYPES = [
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('temporary', 'Temporary'),
        ('intern', 'Intern'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    designation = models.CharField(max_length=100)
    employee_type = models.CharField(max_length=20, choices=EMPLOYEE_TYPES)
    employment_status = models.CharField(max_length=20, choices=EMPLOYEE_STATUS, default='active')
    date_of_joining = models.DateField()
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    phone = models.CharField(max_length=20)
    emergency_contact = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    address = models.TextField()
    photo = models.ImageField(upload_to='employees/', null=True, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name() or self.user.username}"

class LeaveType(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    days_per_year = models.IntegerField(default=0)
    carry_forward = models.BooleanField(default=False)
    max_carry_forward = models.IntegerField(default=0)
    requires_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class LeaveApplication(TimeStampedModel):
    LEAVE_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    application_number = models.CharField(max_length=50, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=LEAVE_STATUS, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            last_leave = LeaveApplication.objects.all().order_by('id').last()
            if last_leave:
                last_number = int(last_leave.application_number.split('-')[-1])
                self.application_number = f"LEAVE-{timezone.now().year}-{last_number + 1:05d}"
            else:
                self.application_number = f"LEAVE-{timezone.now().year}-00001"
        
        # Calculate total days
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.total_days = delta.days + 1  # Inclusive
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.application_number} - {self.employee.user.get_full_name()}"

class Attendance(models.Model):
    ATTENDANCE_STATUS = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('leave', 'On Leave'),
        ('holiday', 'Holiday'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='absent')
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['employee', 'date']
    
    @property
    def total_hours(self):
        if self.check_in and self.check_out:
            from datetime import datetime
            check_in_dt = datetime.combine(self.date, self.check_in)
            check_out_dt = datetime.combine(self.date, self.check_out)
            hours = (check_out_dt - check_in_dt).seconds / 3600
            return round(hours, 2)
        return 0
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.date}"

class Shift(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    @property
    def total_hours(self):
        from datetime import datetime, date
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = datetime.combine(date.today(), self.end_time)
        hours = (end_dt - start_dt).seconds / 3600
        
        # Deduct break time if exists
        if self.break_start and self.break_end:
            break_start_dt = datetime.combine(date.today(), self.break_start)
            break_end_dt = datetime.combine(date.today(), self.break_end)
            break_hours = (break_end_dt - break_start_dt).seconds / 3600
            hours -= break_hours
        
        return round(hours, 2)
    
    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

class EmployeeShift(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['employee', 'effective_from']
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.shift.name}"
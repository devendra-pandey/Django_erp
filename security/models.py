from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel
from hr.models import Employee
from inventory.models import Product, Warehouse

class GatePass(TimeStampedModel):
    GATE_PASS_TYPES = [
        ('material_in', 'Material Incoming'),
        ('material_out', 'Material Outgoing'),
        ('vehicle_in', 'Vehicle Incoming'),
        ('vehicle_out', 'Vehicle Outgoing'),
        ('personnel_in', 'Personnel Incoming'),
        ('personnel_out', 'Personnel Outgoing'),
        ('visitor', 'Visitor'),
        ('contractor', 'Contractor'),
        ('tools_equipment', 'Tools/Equipment'),
        ('waste_scrap', 'Waste/Scrap'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    pass_number = models.CharField(max_length=50, unique=True)
    pass_type = models.CharField(max_length=20, choices=GATE_PASS_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Person/Vehicle Details
    person_name = models.CharField(max_length=200, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    vehicle_number = models.CharField(max_length=50, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    purpose = models.TextField()
    
    # Time Details
    expected_in_date = models.DateTimeField(null=True, blank=True)
    expected_out_date = models.DateTimeField(null=True, blank=True)
    actual_in_date = models.DateTimeField(null=True, blank=True)
    actual_out_date = models.DateTimeField(null=True, blank=True)
    
    # Department and Employee Details
    department = models.ForeignKey('core.Department', on_delete=models.SET_NULL, null=True, blank=True)
    requesting_employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='gate_passes_requested')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='gate_passes_approved')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Security Details
    security_in_charge = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='gate_passes_security')
    security_remarks = models.TextField(blank=True)
    
    # Location Details
    from_location = models.CharField(max_length=200, blank=True)
    to_location = models.CharField(max_length=200, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Additional Fields
    is_returnable = models.BooleanField(default=False)
    expected_return_date = models.DateField(null=True, blank=True)
    is_hazardous = models.BooleanField(default=False)
    reference_document = models.CharField(max_length=100, blank=True)  # PO No, GR No, etc.
    attachment = models.FileField(upload_to='gate_passes/', null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.pass_number:
            last_pass = GatePass.objects.all().order_by('id').last()
            year = timezone.now().year
            if last_pass:
                last_number = int(last_pass.pass_number.split('-')[-1])
                self.pass_number = f"GP-{year}-{last_number + 1:05d}"
            else:
                self.pass_number = f"GP-{year}-00001"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.pass_number} - {self.get_pass_type_display()}"
    
    @property
    def duration_hours(self):
        if self.actual_in_date and self.actual_out_date:
            delta = self.actual_out_date - self.actual_in_date
            return delta.total_seconds() / 3600
        return None

class GatePassItem(models.Model):
    gate_pass = models.ForeignKey(GatePass, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    item_description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_of_measure = models.CharField(max_length=20)
    serial_number = models.CharField(max_length=100, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.gate_pass.pass_number} - {self.item_description}"

class GatePassApproval(models.Model):
    gate_pass = models.ForeignKey(GatePass, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(Employee, on_delete=models.PROTECT)
    approval_level = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('on_hold', 'On Hold'),
    ])
    comments = models.TextField(blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['gate_pass', 'approval_level']
    
    def __str__(self):
        return f"{self.gate_pass.pass_number} - Level {self.approval_level}"

class VisitorLog(models.Model):
    gate_pass = models.ForeignKey(GatePass, on_delete=models.SET_NULL, null=True, blank=True)
    visitor_name = models.CharField(max_length=200)
    visitor_company = models.CharField(max_length=200, blank=True)
    contact_number = models.CharField(max_length=20)
    visiting_person = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='visitors')
    purpose = models.TextField()
    check_in_time = models.DateTimeField()
    check_out_time = models.DateTimeField(null=True, blank=True)
    security_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    visitor_card_issued = models.CharField(max_length=50, blank=True)
    visitor_card_returned = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.visitor_name} - {self.check_in_time.strftime('%Y-%m-%d %H:%M')}"
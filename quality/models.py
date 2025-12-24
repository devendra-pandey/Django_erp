from django.db import models
from core.models import TimeStampedModel
from production.models import ProductionOrder
from procurement.models import GoodsReceiptItem

class QualityCheck(TimeStampedModel):
    QC_TYPES = [
        ('incoming', 'Incoming Material'),
        ('in_process', 'In-Process'),
        ('final', 'Final Inspection'),
        ('outgoing', 'Outgoing'),
    ]
    
    QC_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('quarantine', 'Quarantine'),
    ]
    
    qc_number = models.CharField(max_length=50, unique=True)
    qc_type = models.CharField(max_length=20, choices=QC_TYPES)
    reference_type = models.CharField(max_length=20, choices=[
        ('production', 'Production Order'),
        ('purchase', 'Purchase Order'),
        ('other', 'Other'),
    ])
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, 
                                        null=True, blank=True)
    goods_receipt_item = models.ForeignKey(GoodsReceiptItem, on_delete=models.CASCADE,
                                          null=True, blank=True)
    inspector = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    inspection_date = models.DateField()
    status = models.CharField(max_length=20, choices=QC_STATUS, default='pending')
    remarks = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.qc_number:
            last_qc = QualityCheck.objects.all().order_by('id').last()
            if last_qc:
                last_number = int(last_qc.qc_number.split('-')[-1])
                self.qc_number = f"QC-{timezone.now().year}-{last_number + 1:05d}"
            else:
                self.qc_number = f"QC-{timezone.now().year}-00001"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.qc_number}"

class QualityParameter(models.Model):
    PARAMETER_TYPES = [
        ('visual', 'Visual'),
        ('dimensional', 'Dimensional'),
        ('physical', 'Physical'),
        ('chemical', 'Chemical'),
        ('performance', 'Performance'),
    ]
    
    name = models.CharField(max_length=100)
    parameter_type = models.CharField(max_length=20, choices=PARAMETER_TYPES)
    uom = models.CharField(max_length=20, blank=True)
    min_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    target_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class QualityCheckItem(models.Model):
    quality_check = models.ForeignKey(QualityCheck, on_delete=models.CASCADE, related_name='items')
    parameter = models.ForeignKey(QualityParameter, on_delete=models.PROTECT)
    measured_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    result = models.CharField(max_length=20, choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'N/A'),
    ], default='na')
    remarks = models.TextField(blank=True)
    
    @property
    def is_within_spec(self):
        if self.measured_value is None:
            return False
        
        if self.parameter.min_value and self.measured_value < self.parameter.min_value:
            return False
        if self.parameter.max_value and self.measured_value > self.parameter.max_value:
            return False
        
        return True
    
    def __str__(self):
        return f"{self.parameter.name}: {self.measured_value}"

class NonConformanceReport(TimeStampedModel):
    NCR_STATUS = [
        ('open', 'Open'),
        ('investigation', 'Under Investigation'),
        ('corrective', 'Corrective Action'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
    ]
    
    ncr_number = models.CharField(max_length=50, unique=True)
    quality_check = models.ForeignKey(QualityCheck, on_delete=models.CASCADE)
    severity = models.CharField(max_length=20, choices=[
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ], default='minor')
    description = models.TextField()
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    preventive_action = models.TextField(blank=True)
    responsible_person = models.ForeignKey('auth.User', on_delete=models.PROTECT, 
                                         related_name='ncr_responsible')
    target_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=NCR_STATUS, default='open')
    
    def __str__(self):
        return f"{self.ncr_number}"
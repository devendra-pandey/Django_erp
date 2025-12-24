from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel

class ReportTemplate(TimeStampedModel):
    REPORT_TYPES = [
        ('inventory', 'Inventory Report'),
        ('production', 'Production Report'),
        ('sales', 'Sales Report'),
        ('financial', 'Financial Report'),
        ('quality', 'Quality Report'),
        ('attendance', 'Attendance Report'),
    ]
    
    FORMAT_TYPES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
    ]
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    template_file = models.FileField(upload_to='report_templates/', null=True, blank=True)
    output_format = models.CharField(max_length=10, choices=FORMAT_TYPES, default='pdf')
    parameters = models.JSONField(default=dict)  # Store report parameters as JSON
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class SavedReport(TimeStampedModel):
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    report_name = models.CharField(max_length=200)
    parameters = models.JSONField(default=dict)
    generated_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    generated_date = models.DateTimeField(default=timezone.now)
    report_file = models.FileField(upload_to='saved_reports/', null=True, blank=True)
    file_size = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.report_name} - {self.generated_date}"
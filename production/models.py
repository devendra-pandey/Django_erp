from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel

class WorkCenter(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    department = models.ForeignKey('core.Department', on_delete=models.SET_NULL, null=True, blank=True)
    supervisor = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True)
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    capacity_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class BillOfMaterials(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True)
    finished_product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE,
                                         related_name='bom_as_finished')
    version = models.CharField(max_length=10, default='1.0')
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField()
    production_time = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # hours per unit
    scrap_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percentage
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.code} - {self.finished_product.name} (v{self.version})"

class BOMLine(models.Model):
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, 
                           related_name='lines')
    component = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_of_measure = models.ForeignKey('inventory.UnitOfMeasure', 
                                       on_delete=models.PROTECT)
    scrap_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    operation = models.ForeignKey('Operation', on_delete=models.SET_NULL, 
                                 null=True, blank=True)
    
    @property
    def required_quantity_with_scrap(self):
        if self.scrap_percentage > 0:
            return self.quantity * (1 + self.scrap_percentage / 100)
        return self.quantity
    
    class Meta:
        unique_together = ['bom', 'component']
    
    def __str__(self):
        return f"{self.bom.code} - {self.component.name}"

class Operation(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    work_center = models.ForeignKey(WorkCenter, on_delete=models.CASCADE)
    setup_time = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # hours
    cycle_time = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # hours per unit
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class ProductionOrder(TimeStampedModel):
    ORDER_STATUS = [
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('released', 'Released'),
        ('in_progress', 'In Progress'),
        ('partially_completed', 'Partially Completed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.PROTECT)
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    uom = models.ForeignKey('inventory.UnitOfMeasure', on_delete=models.PROTECT)
    planned_start = models.DateTimeField()
    planned_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='draft')
    priority = models.IntegerField(default=5)  # 1=Highest, 10=Lowest
    work_center = models.ForeignKey(WorkCenter, on_delete=models.SET_NULL, null=True, blank=True)
    supervisor = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, 
                                 null=True, blank=True, related_name='supervised_orders')
    completed_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rejected_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    production_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    material_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            last_po = ProductionOrder.objects.all().order_by('id').last()
            if last_po:
                last_number = int(last_po.order_number.split('-')[-1])
                self.order_number = f"PROD-{timezone.now().year}-{last_number + 1:05d}"
            else:
                self.order_number = f"PROD-{timezone.now().year}-00001"
        
        # Calculate production time
        if self.bom and self.quantity:
            total_time = self.bom.production_time * self.quantity
            if not self.planned_end and self.planned_start:
                from datetime import timedelta
                self.planned_end = self.planned_start + timedelta(hours=float(total_time))
        
        super().save(*args, **kwargs)
    
    @property
    def progress(self):
        if self.quantity > 0:
            return (self.completed_quantity / self.quantity) * 100
        return 0
    
    @property
    def total_cost(self):
        return self.production_cost + self.material_cost
    
    def __str__(self):
        return f"{self.order_number} - {self.product.name}"

class ProductionOperation(models.Model):
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, 
                                        related_name='operations')
    operation = models.ForeignKey(Operation, on_delete=models.PROTECT)
    sequence = models.IntegerField()
    planned_start = models.DateTimeField()
    planned_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    operator = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, 
                               null=True, blank=True)
    quantity_processed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_good = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_rejected = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    setup_time_actual = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    run_time_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['sequence']
    
    @property
    def efficiency(self):
        if self.run_time_actual > 0 and self.operation.cycle_time > 0:
            standard_time = float(self.quantity_processed) * float(self.operation.cycle_time)
            return (standard_time / float(self.run_time_actual)) * 100
        return 0
    
    def __str__(self):
        return f"{self.production_order.order_number} - {self.operation.name}"

class MaterialConsumption(TimeStampedModel):
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE,
                                        related_name='material_consumptions')
    bom_line = models.ForeignKey(BOMLine, on_delete=models.PROTECT)
    quantity_issued = models.DecimalField(max_digits=10, decimal_places=3)
    quantity_used = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    quantity_returned = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    issued_by = models.ForeignKey('auth.User', on_delete=models.PROTECT, 
                                 related_name='issued_materials')
    issued_from = models.ForeignKey('inventory.Warehouse', on_delete=models.PROTECT)
    issued_date = models.DateTimeField(default=timezone.now)
    
    @property
    def waste_percentage(self):
        if self.quantity_issued > 0:
            waste = self.quantity_issued - self.quantity_used - self.quantity_returned
            return (waste / self.quantity_issued) * 100
        return 0
    
    def __str__(self):
        return f"{self.production_order.order_number} - {self.bom_line.component.name}"
from django.db import models
from core.models import TimeStampedModel, Company
from inventory.models import Product, Warehouse

class Supplier(TimeStampedModel):
    SUPPLIER_TYPES = [
        ('material', 'Raw Material Supplier'),
        ('equipment', 'Equipment Supplier'),
        ('service', 'Service Provider'),
        ('other', 'Other'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    supplier_type = models.CharField(max_length=20, choices=SUPPLIER_TYPES, default='material')
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    tax_id = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(max_length=100, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class PurchaseOrder(TimeStampedModel):
    ORDER_STATUS = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('confirmed', 'Confirmed'),
        ('partial', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
        ('closed', 'Closed'),
    ]
    
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    order_date = models.DateField()
    expected_delivery = models.DateField()
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='draft')
    delivery_address = models.TextField()
    terms_conditions = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            last_po = PurchaseOrder.objects.all().order_by('id').last()
            if last_po:
                last_number = int(last_po.po_number.split('-')[-1])
                self.po_number = f"PO-{timezone.now().year}-{last_number + 1:05d}"
            else:
                self.po_number = f"PO-{timezone.now().year}-00001"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    received_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    
    @property
    def subtotal(self):
        return self.quantity * self.unit_price
    
    @property
    def tax_amount(self):
        return self.subtotal * (self.tax_rate / 100)
    
    @property
    def total(self):
        return self.subtotal + self.tax_amount
    
    class Meta:
        unique_together = ['purchase_order', 'product']
    
    def __str__(self):
        return f"{self.product.SKU} - {self.quantity}"

class GoodsReceipt(TimeStampedModel):
    gr_number = models.CharField(max_length=50, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT)
    receipt_date = models.DateField()
    received_by = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.gr_number}"

class GoodsReceiptItem(models.Model):
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='items')
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.PROTECT)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=3)
    batch_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    quality_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending QC'),
        ('passed', 'Passed'),
        ('rejected', 'Rejected'),
        ('quarantine', 'Quarantine')
    ], default='pending')
    
    def __str__(self):
        return f"{self.po_item.product.SKU} - {self.quantity_received}"
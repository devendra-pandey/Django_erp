from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                  null=True, related_name='created_%(class)s')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                  null=True, related_name='updated_%(class)s')
    
    class Meta:
        abstract = True

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, 
                              null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10)
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"

class Product(TimeStampedModel):
    SKU = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    type_choices = [
        ('raw', 'Raw Material'),
        ('finished', 'Finished Goods'),
        ('semi', 'Semi-Finished'),
        ('consumable', 'Consumable'),
    ]
    product_type = models.CharField(max_length=20, choices=type_choices)
    min_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.SKU} - {self.name}"

class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    location = models.CharField(max_length=200)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Changed from hr.Employee to User
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    reserved_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'warehouse']
    
    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity
    
    def __str__(self):
        return f"{self.product.SKU} - {self.warehouse.name}: {self.quantity}"

class StockTransaction(TimeStampedModel):
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJ', 'Adjustment'),
        ('TRF', 'Transfer'),
    ]
    transaction_type = models.CharField(max_length=5, choices=TRANSACTION_TYPES)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    reference_no = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.product.SKU} - {self.quantity}"
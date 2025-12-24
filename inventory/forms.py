from django import forms
from .models import Product, Category, UnitOfMeasure, Warehouse, StockTransaction

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'SKU', 'name', 'description', 'category', 
            'product_type', 'unit_of_measure',
            'min_stock', 'max_stock', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'SKU': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter SKU'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'product_type': forms.Select(attrs={'class': 'form-control'}),
            'unit_of_measure': forms.Select(attrs={'class': 'form-control'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'SKU': 'Product SKU',
            'name': 'Product Name',
            'product_type': 'Product Type',
            'unit_of_measure': 'Unit of Measure',
            'is_active': 'Active Status',
        }
        help_texts = {
            'SKU': 'Unique identifier for the product',
            'min_stock': 'Minimum stock level for alerts',
            'max_stock': 'Maximum stock capacity',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make SKU required
        self.fields['SKU'].required = True
        self.fields['name'].required = True
        self.fields['unit_of_measure'].required = True
        
        # Add placeholder for description
        self.fields['description'].widget.attrs['placeholder'] = 'Enter product description'

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'code', 'location', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'manager': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['product', 'warehouse', 'transaction_type', 'quantity', 'reference_no', 'remarks']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'reference_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional reference number'}),
            'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Add any notes here...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active products and warehouses
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True)
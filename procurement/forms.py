from django import forms
from .models import PurchaseOrder, PurchaseOrderItem, Supplier, GoodsReceipt
from django.forms import inlineformset_factory

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'payment_terms': forms.Textarea(attrs={'rows': 2}),
        }

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'order_date', 'expected_delivery', 
                 'delivery_address', 'terms_conditions', 'notes']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_delivery': forms.DateInput(attrs={'type': 'date'}),
            'delivery_address': forms.Textarea(attrs={'rows': 3}),
            'terms_conditions': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity', 'unit_price', 'tax_rate', 'warehouse']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.001'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'step': '0.01'}),
        }

PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    extra=5,
    can_delete=True
)

class GoodsReceiptForm(forms.ModelForm):
    class Meta:
        model = GoodsReceipt
        fields = ['purchase_order', 'receipt_date', 'received_by', 'warehouse', 'notes']
        widgets = {
            'receipt_date': forms.DateInput(attrs={'type': 'date'}),
        }
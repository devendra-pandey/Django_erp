from django import forms
from .models import BillOfMaterials, BOMLine, ProductionOrder, WorkCenter, Operation
from django.forms import inlineformset_factory

class BOMForm(forms.ModelForm):
    class Meta:
        model = BillOfMaterials
        fields = ['code', 'finished_product', 'version', 'effective_date', 
                 'production_time', 'scrap_rate', 'notes', 'is_active']
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
            'production_time': forms.NumberInput(attrs={'step': '0.01'}),
            'scrap_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class to all fields
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'

class BOMLineForm(forms.ModelForm):
    class Meta:
        model = BOMLine
        fields = ['component', 'quantity', 'unit_of_measure', 'scrap_percentage', 'operation']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.001'}),
            'scrap_percentage': forms.NumberInput(attrs={'step': '0.01'}),
        }

BOMLineFormSet = inlineformset_factory(
    BillOfMaterials, BOMLine,
    form=BOMLineForm,
    extra=5,
    can_delete=True
)

class ProductionOrderForm(forms.ModelForm):
    class Meta:
        model = ProductionOrder
        fields = ['bom', 'product', 'quantity', 'uom', 'planned_start', 
                 'planned_end', 'priority', 'work_center', 'supervisor', 'notes']
        widgets = {
            'planned_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'planned_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'priority': forms.NumberInput(attrs={'min': 1, 'max': 10}),
            'quantity': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class to all fields
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'

class WorkCenterForm(forms.ModelForm):
    class Meta:
        model = WorkCenter
        fields = ['code', 'name', 'description', 'department', 'supervisor', 
                 'cost_per_hour', 'capacity_per_hour', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'cost_per_hour': forms.NumberInput(attrs={'step': '0.01'}),
            'capacity_per_hour': forms.NumberInput(attrs={'step': '0.01'}),
        }

class OperationForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = ['code', 'name', 'description', 'work_center', 'setup_time', 
                 'cycle_time', 'cost_per_hour', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'setup_time': forms.NumberInput(attrs={'step': '0.01'}),
            'cycle_time': forms.NumberInput(attrs={'step': '0.01'}),
            'cost_per_hour': forms.NumberInput(attrs={'step': '0.01'}),
        }
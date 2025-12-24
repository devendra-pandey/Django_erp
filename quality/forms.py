from django import forms
from .models import QualityCheck, QualityCheckItem, QualityParameter, NonConformanceReport
from django.forms import inlineformset_factory

class QualityCheckForm(forms.ModelForm):
    class Meta:
        model = QualityCheck
        fields = ['qc_type', 'reference_type', 'production_order', 
                 'goods_receipt_item', 'inspector', 'inspection_date', 'remarks']
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'

class QualityCheckItemForm(forms.ModelForm):
    class Meta:
        model = QualityCheckItem
        fields = ['parameter', 'measured_value', 'result', 'remarks']
        widgets = {
            'measured_value': forms.NumberInput(attrs={'step': '0.001'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'

QualityCheckItemFormSet = inlineformset_factory(
    QualityCheck, QualityCheckItem,
    form=QualityCheckItemForm,
    extra=3,
    can_delete=True
)

class QualityParameterForm(forms.ModelForm):
    class Meta:
        model = QualityParameter
        fields = ['name', 'parameter_type', 'uom', 'min_value', 
                 'max_value', 'target_value', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'min_value': forms.NumberInput(attrs={'step': '0.001'}),
            'max_value': forms.NumberInput(attrs={'step': '0.001'}),
            'target_value': forms.NumberInput(attrs={'step': '0.001'}),
        }

class NCRForm(forms.ModelForm):
    class Meta:
        model = NonConformanceReport
        fields = ['quality_check', 'severity', 'description', 'root_cause', 
                 'corrective_action', 'preventive_action', 'responsible_person', 
                 'target_date', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'root_cause': forms.Textarea(attrs={'rows': 3}),
            'corrective_action': forms.Textarea(attrs={'rows': 3}),
            'preventive_action': forms.Textarea(attrs={'rows': 3}),
            'target_date': forms.DateInput(attrs={'type': 'date'}),
        }
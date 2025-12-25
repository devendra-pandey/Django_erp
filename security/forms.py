from django import forms
from django.utils import timezone
from .models import GatePass, GatePassItem, VisitorLog
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML, Div

class GatePassForm(forms.ModelForm):
    class Meta:
        model = GatePass
        fields = [
            'pass_type', 'person_name', 'company_name', 'contact_number', 'email',
            'vehicle_number', 'driver_name', 'purpose', 'expected_in_date',
            'expected_out_date', 'department', 'requesting_employee',
            'from_location', 'to_location', 'warehouse', 'is_returnable',
            'expected_return_date', 'is_hazardous', 'reference_document',
            'attachment'
        ]
        widgets = {
            'expected_in_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expected_out_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expected_return_date': forms.DateInput(attrs={'type': 'date'}),
            'purpose': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Basic Information',
                Row(
                    Column('pass_type', css_class='form-group col-md-6'),
                    Column('department', css_class='form-group col-md-6'),
                ),
                Row(
                    Column('requesting_employee', css_class='form-group col-md-6'),
                ),
                Row(
                    Column('person_name', css_class='form-group col-md-6'),
                    Column('company_name', css_class='form-group col-md-6'),
                ),
                Row(
                    Column('contact_number', css_class='form-group col-md-4'),
                    Column('email', css_class='form-group col-md-4'),
                    Column('vehicle_number', css_class='form-group col-md-4'),
                ),
                'driver_name',
                'purpose',
            ),
            Fieldset(
                'Timing Details',
                Row(
                    Column('expected_in_date', css_class='form-group col-md-6'),
                    Column('expected_out_date', css_class='form-group col-md-6'),
                ),
                Row(
                    Column('is_returnable', css_class='form-group col-md-6'),
                    Column('expected_return_date', css_class='form-group col-md-6'),
                ),
            ),
            Fieldset(
                'Location & Additional Details',
                Row(
                    Column('from_location', css_class='form-group col-md-6'),
                    Column('to_location', css_class='form-group col-md-6'),
                ),
                'warehouse',
                Row(
                    Column('is_hazardous', css_class='form-group col-md-4'),
                    Column('reference_document', css_class='form-group col-md-8'),
                ),
                'attachment',
            ),
            Submit('submit', 'Save Gate Pass', css_class='btn btn-primary')
        )

class GatePassItemForm(forms.ModelForm):
    class Meta:
        model = GatePassItem
        fields = ['product', 'item_description', 'quantity', 'unit_of_measure', 
                  'serial_number', 'batch_number', 'value', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

GatePassItemFormSet = forms.inlineformset_factory(
    GatePass, GatePassItem,
    form=GatePassItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)

class SecurityCheckForm(forms.ModelForm):
    class Meta:
        model = GatePass
        fields = ['security_in_charge', 'security_remarks', 'actual_in_date', 'actual_out_date']
        widgets = {
            'actual_in_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'actual_out_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'security_remarks': forms.Textarea(attrs={'rows': 3}),
        }

class VisitorLogForm(forms.ModelForm):
    class Meta:
        model = VisitorLog
        fields = ['visitor_name', 'visitor_company', 'contact_number', 
                  'visiting_person', 'purpose', 'visitor_card_issued']
        widgets = {
            'purpose': forms.Textarea(attrs={'rows': 3}),
        }
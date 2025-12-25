from django.contrib import admin
from .models import GatePass, GatePassItem, VisitorLog

@admin.register(GatePass)
class GatePassAdmin(admin.ModelAdmin):
    list_display = ('pass_number', 'pass_type', 'status', 'person_name', 
                    'vehicle_number', 'created_at', 'requesting_employee')
    list_filter = ('pass_type', 'status', 'department', 'created_at')
    search_fields = ('pass_number', 'person_name', 'company_name', 'vehicle_number')
    readonly_fields = ('pass_number', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

@admin.register(GatePassItem)
class GatePassItemAdmin(admin.ModelAdmin):
    list_display = ('gate_pass', 'item_description', 'quantity', 'unit_of_measure')
    list_filter = ('unit_of_measure',)

@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = ('visitor_name', 'visitor_company', 'visiting_person', 
                    'check_in_time', 'check_out_time')
    list_filter = ('check_in_time',)
    search_fields = ('visitor_name', 'visitor_company', 'contact_number')
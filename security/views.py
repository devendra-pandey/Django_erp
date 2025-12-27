from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa
import datetime
import json

from .models import GatePass, GatePassItem, VisitorLog, GatePassApproval
from .forms import GatePassForm, GatePassItemFormSet, SecurityCheckForm, VisitorLogForm

class GatePassListView(LoginRequiredMixin, ListView):
    model = GatePass
    template_name = 'security/gatepass_list.html'
    context_object_name = 'gate_passes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by type if provided
        pass_type = self.request.GET.get('type')
        if pass_type:
            queryset = queryset.filter(pass_type=pass_type)
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by date range if provided
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__range=[start_date, end_date]
            )
        
        queryset = queryset.order_by('-created_at')
        # Order by creation date (newest first)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter choices to context
        context['pass_types'] = GatePass.GATE_PASS_TYPES
        context['status_choices'] = GatePass.STATUS_CHOICES
        
        return context


class GatePassCreateView(LoginRequiredMixin, CreateView):
    model = GatePass
    form_class = GatePassForm
    template_name = 'security/gatepass_form.html'
    success_url = reverse_lazy('gatepass_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = GatePassItemFormSet(self.request.POST)
        else:
            context['item_formset'] = GatePassItemFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if item_formset.is_valid():
            # Set requesting employee from logged-in user
            if hasattr(self.request.user, 'employee'):
                form.instance.requesting_employee = self.request.user.employee
            else:
                # Handle case where user doesn't have employee profile
                messages.warning(self.request, "User doesn't have employee profile. Please contact admin.")
                return self.form_invalid(form)
            
            self.object = form.save()
            item_formset.instance = self.object
            item_formset.save()
            
            messages.success(self.request, f'Gate Pass {self.object.pass_number} created successfully!')
            return redirect('gatepass_detail', pk=self.object.pk)
        else:
            messages.error(self.request, 'Please correct the errors below.')
            return self.form_invalid(form)

class GatePassDetailView(LoginRequiredMixin, DetailView):
    model = GatePass
    template_name = 'security/gatepass_detail.html'
    context_object_name = 'gate_pass'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['security_form'] = SecurityCheckForm(instance=self.object)
        context['approvals'] = self.object.approvals.all().order_by('approval_level')
        return context

class GatePassUpdateView(LoginRequiredMixin, UpdateView):
    model = GatePass
    form_class = GatePassForm
    template_name = 'security/gatepass_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = GatePassItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = GatePassItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if item_formset.is_valid():
            self.object = form.save()
            item_formset.instance = self.object
            item_formset.save()
            
            messages.success(self.request, f'Gate Pass {self.object.pass_number} updated successfully!')
            return redirect('gatepass_detail', pk=self.object.pk)
        else:
            messages.error(self.request, 'Please correct the errors below.')
            return self.form_invalid(form)

class SecurityCheckInView(LoginRequiredMixin, UpdateView):
    model = GatePass
    form_class = SecurityCheckForm
    template_name = 'security/security_check.html'
    
    def form_valid(self, form):
        gate_pass = form.save(commit=False)
        gate_pass.security_in_charge = self.request.user
        gate_pass.actual_in_date = timezone.now()
        gate_pass.status = 'in_progress'
        gate_pass.save()
        
        messages.success(self.request, f'Check-in recorded for {gate_pass.pass_number}')
        return redirect('gatepass_detail', pk=gate_pass.pk)

class SecurityCheckOutView(LoginRequiredMixin, UpdateView):
    model = GatePass
    form_class = SecurityCheckForm
    template_name = 'security/security_check.html'
    
    def form_valid(self, form):
        gate_pass = form.save(commit=False)
        gate_pass.security_in_charge = self.request.user
        gate_pass.actual_out_date = timezone.now()
        gate_pass.status = 'completed'
        gate_pass.save()
        
        messages.success(self.request, f'Check-out recorded for {gate_pass.pass_number}')
        return redirect('gatepass_detail', pk=gate_pass.pk)

class PrintGatePassView(LoginRequiredMixin, DetailView):
    model = GatePass
    template_name = 'security/gatepass_print.html'
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        
        # For PDF generation
        if request.GET.get('format') == 'pdf':
            return self.generate_pdf(context)
        
        # For HTML preview
        return render(request, self.template_name, context)
    
    def generate_pdf(self, context):
        template = get_template(self.template_name)
        html = template.render(context)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="GatePass_{self.object.pass_number}.pdf"'
        
        pisa_status = pisa.CreatePDF(
            html, dest=response,
            encoding='UTF-8'
        )
        
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response

class UpdateGatePassStatus(LoginRequiredMixin, View):
    """API view to update gate pass status"""
    
    def post(self, request, pk):
        try:
            gate_pass = GatePass.objects.get(pk=pk)
            data = json.loads(request.body) if request.body else {}
            new_status = data.get('status', request.POST.get('status'))
            remarks = data.get('remarks', request.POST.get('remarks', ''))
            
            if new_status not in dict(GatePass.STATUS_CHOICES):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid status'
                }, status=400)
            
            # Update gate pass
            gate_pass.status = new_status
            if remarks:
                gate_pass.security_remarks = remarks
            gate_pass.security_in_charge = request.user
            
            # Set timestamps based on status
            if new_status == 'in_progress' and not gate_pass.actual_in_date:
                gate_pass.actual_in_date = timezone.now()
            elif new_status == 'completed' and not gate_pass.actual_out_date:
                gate_pass.actual_out_date = timezone.now()
            
            gate_pass.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Status updated to {gate_pass.get_status_display()}',
                'status': gate_pass.status,
                'status_display': gate_pass.get_status_display(),
                'actual_in_date': gate_pass.actual_in_date.strftime('%Y-%m-%d %H:%M:%S') if gate_pass.actual_in_date else None,
                'actual_out_date': gate_pass.actual_out_date.strftime('%Y-%m-%d %H:%M:%S') if gate_pass.actual_out_date else None,
            })
            
        except GatePass.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Gate pass not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'security/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        
        # Statistics
        context['total_passes'] = GatePass.objects.count()
        context['today_passes'] = GatePass.objects.filter(
            created_at__date=today
        ).count()
        context['pending_passes'] = GatePass.objects.filter(
            status='pending'
        ).count()
        context['in_progress_passes'] = GatePass.objects.filter(
            status='in_progress'
        ).count()
        
        # Recent activities
        context['recent_passes'] = GatePass.objects.all().order_by('-created_at')[:10]
        context['visitors_today'] = VisitorLog.objects.filter(
            check_in_time__date=today
        )
        
        # Status counts
        context['status_counts'] = {
            'pending': GatePass.objects.filter(status='pending').count(),
            'approved': GatePass.objects.filter(status='approved').count(),
            'in_progress': GatePass.objects.filter(status='in_progress').count(),
            'completed': GatePass.objects.filter(status='completed').count(),
            'cancelled': GatePass.objects.filter(status='cancelled').count(),
        }
        
        return context

class VisitorLogView(LoginRequiredMixin, ListView):
    model = VisitorLog
    template_name = 'security/visitor_log.html'
    context_object_name = 'visitors'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date if provided
        date = self.request.GET.get('date')
        if date:
            queryset = queryset.filter(check_in_time__date=date)
        
        # Filter by visitor name if provided
        name = self.request.GET.get('name')
        if name:
            queryset = queryset.filter(visitor_name__icontains=name)
        
        return queryset.order_by('-check_in_time')

class VisitorCheckInView(LoginRequiredMixin, CreateView):
    model = VisitorLog
    form_class = VisitorLogForm
    template_name = 'security/visitor_checkin.html'
    success_url = reverse_lazy('visitor_log')
    
    def form_valid(self, form):
        visitor = form.save(commit=False)
        visitor.check_in_time = timezone.now()
        visitor.security_officer = self.request.user
        
        # Generate visitor card number
        today = timezone.now().date()
        last_visitor_today = VisitorLog.objects.filter(
            check_in_time__date=today
        ).order_by('-id').first()
        
        if last_visitor_today and last_visitor_today.visitor_card_issued:
            last_number = int(last_visitor_today.visitor_card_issued.split('-')[-1])
            visitor.visitor_card_issued = f"VC-{today.strftime('%Y%m%d')}-{last_number + 1:03d}"
        else:
            visitor.visitor_card_issued = f"VC-{today.strftime('%Y%m%d')}-001"
        
        visitor.save()
        
        messages.success(self.request, f'Visitor {visitor.visitor_name} checked in successfully! Visitor Card: {visitor.visitor_card_issued}')
        return super().form_valid(form)

class VisitorCheckOutView(LoginRequiredMixin, UpdateView):
    model = VisitorLog
    fields = []
    template_name = 'security/visitor_checkout.html'
    success_url = reverse_lazy('visitor_log')
    
    def form_valid(self, form):
        visitor = form.save(commit=False)
        visitor.check_out_time = timezone.now()
        visitor.visitor_card_returned = True
        visitor.save()
        
        messages.success(self.request, f'Visitor {visitor.visitor_name} checked out successfully!')
        return super().form_valid(form)
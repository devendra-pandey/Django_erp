from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import BillOfMaterials, ProductionOrder, WorkCenter, Operation, BOMLine
from .forms import BOMForm, BOMLineFormSet, ProductionOrderForm, WorkCenterForm, OperationForm

class BOMListView(LoginRequiredMixin, ListView):
    model = BillOfMaterials
    template_name = 'production/bom_list.html'
    context_object_name = 'boms'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = BillOfMaterials.objects.select_related('finished_product').all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(finished_product__name__icontains=search) |
                Q(finished_product__SKU__icontains=search)
            )
        active = self.request.GET.get('active')
        if active == 'true':
            queryset = queryset.filter(is_active=True)
        elif active == 'false':
            queryset = queryset.filter(is_active=False)
        return queryset.order_by('-created_at')

class BOMCreateView(LoginRequiredMixin, CreateView):
    model = BillOfMaterials
    form_class = BOMForm
    template_name = 'production/bom_form.html'
    success_url = reverse_lazy('production:bom_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = BOMLineFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = BOMLineFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save(commit=False)
            self.object.created_by = self.request.user
            self.object.save()
            
            formset.instance = self.object
            formset.save()
            
            messages.success(self.request, 'BOM created successfully!')
            return redirect('production:bom_detail', pk=self.object.pk)
        
        return self.form_invalid(form)

class BOMDetailView(LoginRequiredMixin, DetailView):
    model = BillOfMaterials
    template_name = 'production/bom_detail.html'
    context_object_name = 'bom'

class BOMUpdateView(LoginRequiredMixin, UpdateView):
    model = BillOfMaterials
    form_class = BOMForm
    template_name = 'production/bom_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = BOMLineFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = BOMLineFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save(commit=False)
            self.object.updated_by = self.request.user
            self.object.save()
            
            formset.instance = self.object
            formset.save()
            
            messages.success(self.request, 'BOM updated successfully!')
            return redirect('production:bom_detail', pk=self.object.pk)
        
        return self.form_invalid(form)

class BOMDeleteView(LoginRequiredMixin, DeleteView):
    model = BillOfMaterials
    template_name = 'production/bom_confirm_delete.html'
    success_url = reverse_lazy('production:bom_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'BOM deleted successfully!')
        return super().delete(request, *args, **kwargs)

class ProductionOrderListView(LoginRequiredMixin, ListView):
    model = ProductionOrder
    template_name = 'production/order_list.html'
    context_object_name = 'orders'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = ProductionOrder.objects.select_related('product', 'bom').all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(product__name__icontains=search)
            )
        return queryset.order_by('-created_at')

class ProductionOrderCreateView(LoginRequiredMixin, CreateView):
    model = ProductionOrder
    form_class = ProductionOrderForm
    template_name = 'production/order_form.html'
    success_url = reverse_lazy('production:order_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Production order created successfully!')
        return super().form_valid(form)

class ProductionOrderDetailView(LoginRequiredMixin, DetailView):
    model = ProductionOrder
    template_name = 'production/order_detail.html'
    context_object_name = 'order'

class ProductionOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductionOrder
    form_class = ProductionOrderForm
    template_name = 'production/order_form.html'
    success_url = reverse_lazy('production:order_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Production order updated successfully!')
        return super().form_valid(form)

class ProductionOrderDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductionOrder
    template_name = 'production/order_confirm_delete.html'
    success_url = reverse_lazy('production:order_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Production order deleted successfully!')
        return super().delete(request, *args, **kwargs)

class WorkCenterListView(LoginRequiredMixin, ListView):
    model = WorkCenter
    template_name = 'production/workcenter_list.html'
    context_object_name = 'workcenters'

class WorkCenterCreateView(LoginRequiredMixin, CreateView):
    model = WorkCenter
    form_class = WorkCenterForm
    template_name = 'production/workcenter_form.html'
    success_url = reverse_lazy('production:workcenter_list')

class OperationListView(LoginRequiredMixin, ListView):
    model = Operation
    template_name = 'production/operation_list.html'
    context_object_name = 'operations'

class OperationCreateView(LoginRequiredMixin, CreateView):
    model = Operation
    form_class = OperationForm
    template_name = 'production/operation_form.html'
    success_url = reverse_lazy('production:operation_list')

def start_production_order(request, pk):
    """Start a production order"""
    order = get_object_or_404(ProductionOrder, pk=pk)
    if order.status == 'released':
        order.status = 'in_progress'
        order.actual_start = timezone.now()
        order.save()
        messages.success(request, f'Production order {order.order_number} started!')
    else:
        messages.error(request, 'Only released orders can be started.')
    return redirect('production:order_detail', pk=order.pk)

def complete_production_order(request, pk):
    """Complete a production order"""
    order = get_object_or_404(ProductionOrder, pk=pk)
    if order.status == 'in_progress':
        order.status = 'completed'
        order.actual_end = timezone.now()
        order.completed_quantity = order.quantity  # For demo, assume all completed
        order.save()
        messages.success(request, f'Production order {order.order_number} completed!')
    else:
        messages.error(request, 'Only in-progress orders can be completed.')
    return redirect('production:order_detail', pk=order.pk)

def production_dashboard(request):
    """Production dashboard view"""
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Get production metrics
    total_orders = ProductionOrder.objects.count()
    active_orders = ProductionOrder.objects.filter(
        status__in=['in_progress', 'released']
    ).count()
    completed_today = ProductionOrder.objects.filter(
        status='completed',
        actual_end__date=today
    ).count()
    
    # Get recent orders
    recent_orders = ProductionOrder.objects.select_related('product').order_by('-created_at')[:10]
    
    # Get production by status
    status_counts = ProductionOrder.objects.values('status').annotate(
        count=Count('id')
    )
    
    context = {
        'total_orders': total_orders,
        'active_orders': active_orders,
        'completed_today': completed_today,
        'recent_orders': recent_orders,
        'status_counts': status_counts,
    }
    
    return render(request, 'production/dashboard.html', context)

def material_issue_view(request, order_id):
    """View for issuing materials for production order"""
    order = get_object_or_404(ProductionOrder, pk=order_id)
    bom_lines = order.bom.lines.select_related('component').all()
    
    # For demo, we'll just show the materials needed
    context = {
        'order': order,
        'bom_lines': bom_lines,
    }
    return render(request, 'production/material_issue.html', context)


def start_operation(request, pk):
    """Start an operation"""
    from .models import ProductionOperation
    operation = get_object_or_404(ProductionOperation, pk=pk)
    operation.status = 'in_progress'
    operation.actual_start = timezone.now()
    operation.save()
    messages.success(request, f'Operation {operation.operation.name} started!')
    return redirect('production:order_detail', pk=operation.production_order.pk)

def complete_operation(request, pk):
    """Complete an operation"""
    from .models import ProductionOperation
    operation = get_object_or_404(ProductionOperation, pk=pk)
    operation.status = 'completed'
    operation.actual_end = timezone.now()
    operation.save()
    messages.success(request, f'Operation {operation.operation.name} completed!')
    return redirect('production:order_detail', pk=operation.production_order.pk)
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import JsonResponse
from .models import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem
from .forms import SupplierForm, PurchaseOrderForm, PurchaseOrderItemFormSet, GoodsReceiptForm

class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'procurement/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Supplier.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(contact_person__icontains=search)
            )
        active = self.request.GET.get('active')
        if active == 'true':
            queryset = queryset.filter(is_active=True)
        elif active == 'false':
            queryset = queryset.filter(is_active=False)
        return queryset.order_by('-created_at')

class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'procurement/supplier_form.html'
    success_url = reverse_lazy('procurement:supplier_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Supplier created successfully!')
        return super().form_valid(form)

class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = 'procurement/supplier_detail.html'
    context_object_name = 'supplier'

class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'procurement/supplier_form.html'
    success_url = reverse_lazy('procurement:supplier_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Supplier updated successfully!')
        return super().form_valid(form)

class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'procurement/supplier_confirm_delete.html'
    success_url = reverse_lazy('procurement:supplier_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Supplier deleted successfully!')
        return super().delete(request, *args, **kwargs)

class PurchaseOrderListView(LoginRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'procurement/purchase_order_list.html'
    context_object_name = 'purchase_orders'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = PurchaseOrder.objects.select_related('supplier').all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        supplier_id = self.request.GET.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(po_number__icontains=search) |
                Q(supplier__name__icontains=search)
            )
        return queryset.order_by('-order_date')

class PurchaseOrderCreateView(LoginRequiredMixin, CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'procurement/purchase_order_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = PurchaseOrderItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = PurchaseOrderItemFormSet(instance=self.object)
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
            
            # Calculate totals
            total = sum(item.total for item in self.object.items.all())
            tax = sum(item.tax_amount for item in self.object.items.all())
            
            self.object.total_amount = total - tax
            self.object.tax_amount = tax
            self.object.grand_total = total
            self.object.save()
            
            messages.success(self.request, 'Purchase order created successfully!')
            return redirect('procurement:purchase_order_detail', pk=self.object.pk)
        
        return self.form_invalid(form)

class PurchaseOrderDetailView(LoginRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'procurement/purchase_order_detail.html'
    context_object_name = 'purchase_order'

class PurchaseOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'procurement/purchase_order_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = PurchaseOrderItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = PurchaseOrderItemFormSet(instance=self.object)
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
            
            # Recalculate totals
            total = sum(item.total for item in self.object.items.all())
            tax = sum(item.tax_amount for item in self.object.items.all())
            
            self.object.total_amount = total - tax
            self.object.tax_amount = tax
            self.object.grand_total = total
            self.object.save()
            
            messages.success(self.request, 'Purchase order updated successfully!')
            return redirect('procurement:purchase_order_detail', pk=self.object.pk)
        
        return self.form_invalid(form)

class PurchaseOrderDeleteView(LoginRequiredMixin, DeleteView):
    model = PurchaseOrder
    template_name = 'procurement/purchase_order_confirm_delete.html'
    success_url = reverse_lazy('procurement:purchase_order_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Purchase order deleted successfully!')
        return super().delete(request, *args, **kwargs)

class GoodsReceiptListView(LoginRequiredMixin, ListView):
    model = GoodsReceipt
    template_name = 'procurement/goods_receipt_list.html'
    context_object_name = 'goods_receipts'

class GoodsReceiptCreateView(LoginRequiredMixin, CreateView):
    model = GoodsReceipt
    form_class = GoodsReceiptForm
    template_name = 'procurement/goods_receipt_form.html'
    success_url = reverse_lazy('procurement:goods_receipt_list')
    
    def form_valid(self, form):
        form.instance.received_by = self.request.user
        messages.success(self.request, 'Goods receipt created successfully!')
        return super().form_valid(form)

class GoodsReceiptDetailView(LoginRequiredMixin, DetailView):
    model = GoodsReceipt
    template_name = 'procurement/goods_receipt_detail.html'
    context_object_name = 'goods_receipt'

def send_purchase_order(request, pk):
    """Send purchase order to supplier"""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if po.status == 'draft':
        po.status = 'sent'
        po.save()
        messages.success(request, f'Purchase order {po.po_number} sent to supplier!')
    else:
        messages.error(request, 'Only draft orders can be sent.')
    return redirect('procurement:purchase_order_detail', pk=po.pk)

def receive_purchase_order(request, pk):
    """Mark purchase order as received"""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if po.status in ['sent', 'confirmed']:
        po.status = 'received'
        po.save()
        messages.success(request, f'Purchase order {po.po_number} marked as received!')
    else:
        messages.error(request, 'Only sent or confirmed orders can be received.')
    return redirect('procurement:purchase_order_detail', pk=po.pk)

def get_po_items(request, po_id):
    """Get PO items for goods receipt (AJAX)"""
    po = get_object_or_404(PurchaseOrder, id=po_id)
    items = []
    
    for item in po.items.all():
        pending = item.quantity - item.received_quantity
        if pending > 0:
            items.append({
                'id': item.id,
                'product': f"{item.product.SKU} - {item.product.name}",
                'ordered': str(item.quantity),
                'received': str(item.received_quantity),
                'pending': str(pending),
                'unit': item.product.unit_of_measure.symbol
            })
    
    return JsonResponse(items, safe=False)

def procurement_dashboard(request):
    """Procurement dashboard view"""
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    # Get purchase metrics
    total_pos = PurchaseOrder.objects.count()
    pending_pos = PurchaseOrder.objects.filter(
        status__in=['draft', 'sent', 'confirmed']
    ).count()
    
    # Monthly spending
    monthly_spending = PurchaseOrder.objects.filter(
        order_date__gte=month_start,
        status__in=['received', 'partial']
    ).aggregate(total=Sum('grand_total'))['total'] or 0
    
    # Active suppliers
    active_suppliers = Supplier.objects.filter(is_active=True).count()
    
    # Recent POs
    recent_pos = PurchaseOrder.objects.select_related('supplier').order_by('-created_at')[:10]
    
    context = {
        'total_pos': total_pos,
        'pending_pos': pending_pos,
        'monthly_spending': monthly_spending,
        'active_suppliers': active_suppliers,
        'recent_pos': recent_pos,
    }
    
    return render(request, 'procurement/dashboard.html', context)
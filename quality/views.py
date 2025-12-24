from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from .models import QualityCheck, QualityParameter, NonConformanceReport
from .forms import QualityCheckForm, QualityParameterForm, NCRForm

class QualityCheckListView(LoginRequiredMixin, ListView):
    model = QualityCheck
    template_name = 'quality/qc_list.html'
    context_object_name = 'quality_checks'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = QualityCheck.objects.all()
        qc_type = self.request.GET.get('qc_type')
        if qc_type:
            queryset = queryset.filter(qc_type=qc_type)
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')

class QualityCheckCreateView(LoginRequiredMixin, CreateView):
    model = QualityCheck
    form_class = QualityCheckForm
    template_name = 'quality/qc_form.html'
    success_url = reverse_lazy('quality:qc_list')
    
    def form_valid(self, form):
        form.instance.inspector = self.request.user
        messages.success(self.request, 'Quality check created successfully!')
        return super().form_valid(form)

class QualityCheckDetailView(LoginRequiredMixin, DetailView):
    model = QualityCheck
    template_name = 'quality/qc_detail.html'
    context_object_name = 'quality_check'

class QualityCheckUpdateView(LoginRequiredMixin, UpdateView):
    model = QualityCheck
    form_class = QualityCheckForm
    template_name = 'quality/qc_form.html'
    success_url = reverse_lazy('quality:qc_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Quality check updated successfully!')
        return super().form_valid(form)

class QualityCheckDeleteView(LoginRequiredMixin, DeleteView):
    model = QualityCheck
    template_name = 'quality/qc_confirm_delete.html'
    success_url = reverse_lazy('quality:qc_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Quality check deleted successfully!')
        return super().delete(request, *args, **kwargs)

class QualityParameterListView(LoginRequiredMixin, ListView):
    model = QualityParameter
    template_name = 'quality/parameter_list.html'
    context_object_name = 'parameters'

class QualityParameterCreateView(LoginRequiredMixin, CreateView):
    model = QualityParameter
    form_class = QualityParameterForm
    template_name = 'quality/parameter_form.html'
    success_url = reverse_lazy('quality:parameter_list')

class NCRListView(LoginRequiredMixin, ListView):
    model = NonConformanceReport
    template_name = 'quality/ncr_list.html'
    context_object_name = 'ncrs'

class NCRCreateView(LoginRequiredMixin, CreateView):
    model = NonConformanceReport
    form_class = NCRForm
    template_name = 'quality/ncr_form.html'
    success_url = reverse_lazy('quality:ncr_list')

class NCRDetailView(LoginRequiredMixin, DetailView):
    model = NonConformanceReport
    template_name = 'quality/ncr_detail.html'
    context_object_name = 'ncr'

class NCRUpdateView(LoginRequiredMixin, UpdateView):
    model = NonConformanceReport
    form_class = NCRForm
    template_name = 'quality/ncr_form.html'
    success_url = reverse_lazy('quality:ncr_list')

def perform_quality_check(request, pk):
    """Perform quality check action"""
    qc = get_object_or_404(QualityCheck, pk=pk)
    if qc.status == 'pending':
        qc.status = 'in_progress'
        qc.save()
        messages.success(request, 'Quality check started!')
    else:
        messages.error(request, 'Only pending checks can be performed.')
    return redirect('quality:qc_detail', pk=qc.pk)

def close_ncr(request, pk):
    """Close NCR"""
    ncr = get_object_or_404(NonConformanceReport, pk=pk)
    ncr.status = 'closed'
    ncr.completion_date = timezone.now()
    ncr.save()
    messages.success(request, 'NCR closed successfully!')
    return redirect('quality:ncr_detail', pk=ncr.pk)

def quality_dashboard(request):
    """Quality dashboard view"""
    total_checks = QualityCheck.objects.count()
    passed_checks = QualityCheck.objects.filter(status='passed').count()
    failed_checks = QualityCheck.objects.filter(status='failed').count()
    
    recent_checks = QualityCheck.objects.order_by('-created_at')[:10]
    recent_ncrs = NonConformanceReport.objects.order_by('-created_at')[:10]
    
    context = {
        'total_checks': total_checks,
        'passed_checks': passed_checks,
        'failed_checks': failed_checks,
        'quality_rate': (passed_checks / total_checks * 100) if total_checks > 0 else 0,
        'recent_checks': recent_checks,
        'recent_ncrs': recent_ncrs,
    }
    
    return render(request, 'quality/dashboard.html', context)

def defect_analysis_report(request):
    """Defect analysis report"""
    # Simplified version
    return render(request, 'quality/reports/defect_analysis.html')

def quality_trends_report(request):
    """Quality trends report"""
    # Simplified version
    return render(request, 'quality/reports/quality_trends.html')
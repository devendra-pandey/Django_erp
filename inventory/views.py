from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category, UnitOfMeasure, Warehouse, Stock
from .forms import ProductForm
from django.db.models import Sum

# Dashboard and main pages
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

# Product Views
@login_required
def product_list(request):
    # Get all products
    products = Product.objects.select_related('category', 'unit_of_measure').all()
    
    # Apply filters
    search = request.GET.get('search')
    category = request.GET.get('category')
    product_type = request.GET.get('type')
    active = request.GET.get('active')
    
    if search:
        products = products.filter(
            Q(SKU__icontains=search) |
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if category:
        products = products.filter(category_id=category)
    
    if product_type:
        products = products.filter(product_type=product_type)
    
    if active == 'true':
        products = products.filter(is_active=True)
    elif active == 'false':
        products = products.filter(is_active=False)
    
    # Order by created date (newest first)
    products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 25)  # Show 25 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter dropdown
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': categories,
        'search': search or '',
        'selected_category': category or '',
        'selected_type': product_type or '',
        'selected_active': active or '',
    }
    return render(request, 'inventory/product_list.html', context)

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            messages.success(request, 'Product created successfully!')
            return redirect('inventory:product_list')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Create New Product'
    }
    return render(request, 'inventory/product_form.html', context)

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related(
        'category', 'unit_of_measure', 'created_by', 'updated_by'
    ), pk=pk)
    
    # Get stock information
    stocks = Stock.objects.filter(product=product).select_related('warehouse')
    
    context = {
        'product': product,
        'stocks': stocks
    }
    return render(request, 'inventory/product_detail.html', context)

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            updated_product = form.save(commit=False)
            updated_product.updated_by = request.user
            updated_product.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('inventory:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'title': 'Update Product'
    }
    return render(request, 'inventory/product_form.html', context)

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('inventory:product_list')
    
    context = {
        'product': product
    }
    return render(request, 'inventory/product_confirm_delete.html', context)

# Stock Views
@login_required
def stock_list(request):
    stocks = Stock.objects.select_related('product', 'warehouse').all()
    
    # Filter by product search
    search = request.GET.get('search')
    if search:
        stocks = stocks.filter(
            Q(product__SKU__icontains=search) |
            Q(product__name__icontains=search)
        )
    
    # Filter by warehouse
    warehouse = request.GET.get('warehouse')
    if warehouse:
        stocks = stocks.filter(warehouse_id=warehouse)
    
    # Order by product name
    stocks = stocks.order_by('product__name')
    
    # Pagination
    paginator = Paginator(stocks, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get warehouses for filter dropdown
    warehouses = Warehouse.objects.all()
    
    context = {
        'page_obj': page_obj,
        'stocks': page_obj.object_list,
        'warehouses': warehouses,
        'search': search or '',
        'selected_warehouse': warehouse or '',
    }
    return render(request, 'inventory/stock_list.html', context)

@login_required
def stock_transaction(request):
    # This would handle stock in/out transactions
    # For now, just show a basic page
    products = Product.objects.filter(is_active=True)
    warehouses = Warehouse.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'warehouses': warehouses
    }
    return render(request, 'inventory/stock_transaction.html', context)

# Category management views
@login_required
def category_list(request):
    categories = Category.objects.all()
    context = {
        'categories': categories
    }
    return render(request, 'inventory/category_list.html', context)

# Warehouse management views
@login_required
def warehouse_list(request):
    warehouses = Warehouse.objects.all()
    context = {
        'warehouses': warehouses
    }
    return render(request, 'inventory/warehouse_list.html', context)
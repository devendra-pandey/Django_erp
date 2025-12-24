from django.contrib import admin
from .models import Category, UnitOfMeasure, Product, Warehouse, Stock, StockTransaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'description']
    search_fields = ['name']
    list_filter = ['parent']

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol']
    search_fields = ['name', 'symbol']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['SKU', 'name', 'category', 'product_type', 'unit_of_measure', 'is_active']
    list_filter = ['product_type', 'is_active', 'category']
    search_fields = ['SKU', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'location', 'manager', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'location']

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'quantity', 'reserved_quantity', 'available_quantity', 'last_updated']
    list_filter = ['warehouse']
    search_fields = ['product__SKU', 'product__name', 'warehouse__name']

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'product', 'warehouse', 'quantity', 'reference_no', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['product__SKU', 'product__name', 'reference_no']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
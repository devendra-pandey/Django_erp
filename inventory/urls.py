from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Product URLs
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/update/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Stock URLs
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/transaction/', views.stock_transaction, name='stock_transaction'),
    
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    
    # Warehouse URLs
    path('warehouses/', views.warehouse_list, name='warehouse_list'),
]
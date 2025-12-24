from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Notification, NotificationPreference
from production.models import ProductionOrder
from inventory.models import Stock, Product
from quality.models import QualityCheck, NonConformanceReport
from procurement.models import PurchaseOrder

@receiver(post_save, sender=ProductionOrder)
def create_production_notifications(sender, instance, created, **kwargs):
    if created:
        # Notify production manager about new order
        notify_users(
            users=User.objects.filter(groups__name='Production Managers'),
            title=f"New Production Order Created",
            message=f"Production order {instance.order_number} has been created for {instance.product.name}.",
            notification_type='info',
            related_model='production.ProductionOrder',
            related_id=instance.id
        )
    elif instance.status_changed:
        # Status change notification
        notify_users(
            users=get_related_users(instance),
            title=f"Production Order Status Changed",
            message=f"Order {instance.order_number} is now {instance.get_status_display()}.",
            notification_type='info',
            related_model='production.ProductionOrder',
            related_id=instance.id
        )

@receiver(post_save, sender=Stock)
def check_low_stock(sender, instance, **kwargs):
    if instance.product.min_stock and instance.quantity < instance.product.min_stock:
        notify_users(
            users=User.objects.filter(groups__name='Inventory Managers'),
            title=f"Low Stock Alert",
            message=f"Product {instance.product.SKU} is below minimum stock level in {instance.warehouse.name}. Current: {instance.quantity}, Min: {instance.product.min_stock}",
            notification_type='warning',
            related_model='inventory.Stock',
            related_id=instance.id
        )

@receiver(post_save, sender=QualityCheck)
def quality_check_notification(sender, instance, created, **kwargs):
    if instance.status == 'failed':
        notify_users(
            users=User.objects.filter(groups__name='Quality Managers'),
            title=f"Quality Check Failed",
            message=f"Quality check {instance.qc_number} has failed. Please review.",
            notification_type='error',
            related_model='quality.QualityCheck',
            related_id=instance.id
        )
    elif instance.status == 'passed':
        notify_users(
            users=get_related_users(instance),
            title=f"Quality Check Passed",
            message=f"Quality check {instance.qc_number} has passed successfully.",
            notification_type='success',
            related_model='quality.QualityCheck',
            related_id=instance.id
        )

@receiver(post_save, sender=PurchaseOrder)
def purchase_order_notifications(sender, instance, created, **kwargs):
    if created:
        notify_users(
            users=User.objects.filter(groups__name='Procurement Managers'),
            title=f"New Purchase Order",
            message=f"Purchase order {instance.po_number} has been created for {instance.supplier.name}.",
            notification_type='info',
            related_model='procurement.PurchaseOrder',
            related_id=instance.id
        )
    elif instance.expected_delivery == timezone.now().date():
        # Delivery reminder
        notify_users(
            users=get_related_users(instance),
            title=f"Delivery Due Today",
            message=f"Purchase order {instance.po_number} is due for delivery today.",
            notification_type='reminder',
            related_model='procurement.PurchaseOrder',
            related_id=instance.id
        )

# Helper functions
def notify_users(users, title, message, notification_type='info', 
                related_model=None, related_id=None, priority=1):
    for user in users:
        # Check user preferences
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        
        if notification_type == 'warning' and not pref.low_stock_alerts:
            continue
        if 'quality' in title.lower() and not pref.quality_alerts:
            continue
        if 'production' in title.lower() and not pref.production_alerts:
            continue
        
        # Create notification
        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            related_model=related_model,
            related_id=related_id,
            priority=priority
        )

def get_related_users(instance):
    """Get users related to an instance (e.g., supervisors, managers)"""
    users = User.objects.filter(is_active=True)
    
    if hasattr(instance, 'created_by'):
        users = users | User.objects.filter(id=instance.created_by.id)
    
    if hasattr(instance, 'supervisor') and instance.supervisor:
        users = users | User.objects.filter(id=instance.supervisor.user.id)
    
    return users.distinct()
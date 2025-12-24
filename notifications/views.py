from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from .models import Notification, NotificationPreference

@login_required
def notifications_list(request):
    """List all notifications for the user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications/list.html', {'notifications': notifications})

@login_required
def unread_notifications(request):
    """List unread notifications"""
    notifications = Notification.objects.filter(
        user=request.user, is_read=False
    ).order_by('-created_at')
    return render(request, 'notifications/unread.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, pk):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Notification marked as read')
    return redirect('notifications:list')

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'All notifications marked as read')
    return redirect('notifications:list')

@login_required
def delete_notification(request, pk):
    """Delete a notification"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Notification deleted')
    return redirect('notifications:list')

@login_required
def clear_all_notifications(request):
    """Clear all notifications"""
    Notification.objects.filter(user=request.user).delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'All notifications cleared')
    return redirect('notifications:list')

@login_required
def notification_preferences(request):
    """View and update notification preferences"""
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update preferences
        preferences.email_notifications = request.POST.get('email_notifications') == 'on'
        preferences.push_notifications = request.POST.get('push_notifications') == 'on'
        preferences.in_app_notifications = request.POST.get('in_app_notifications') == 'on'
        preferences.low_stock_alerts = request.POST.get('low_stock_alerts') == 'on'
        preferences.quality_alerts = request.POST.get('quality_alerts') == 'on'
        preferences.production_alerts = request.POST.get('production_alerts') == 'on'
        preferences.purchase_order_alerts = request.POST.get('purchase_order_alerts') == 'on'
        preferences.attendance_alerts = request.POST.get('attendance_alerts') == 'on'
        preferences.save()
        
        messages.success(request, 'Notification preferences updated')
        return redirect('notifications:preferences')
    
    return render(request, 'notifications/preferences.html', {'preferences': preferences})

@login_required
def update_preferences(request):
    """Update notification preferences via AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
        
        preference_type = request.POST.get('type')
        value = request.POST.get('value') == 'true'
        
        if hasattr(preferences, preference_type):
            setattr(preferences, preference_type, value)
            preferences.save()
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'Invalid preference type'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def unread_notification_count(request):
    """Get unread notification count for AJAX requests"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

# WebSocket consumer (simplified for now)
class NotificationConsumer:
    """Simplified WebSocket consumer"""
    @staticmethod
    def as_asgi():
        return None  # Return None for now, implement properly with Channels later

@login_required
def test_email_notification(request):
    """Test email notification (simplified)"""
    # Create a test notification
    Notification.objects.create(
        user=request.user,
        title="Test Notification",
        message="This is a test notification to verify the system is working.",
        notification_type='info',
        priority=1
    )
    
    messages.success(request, 'Test notification created successfully!')
    return redirect('notifications:list')

# Helper function to create notifications (can be called from other apps)
def create_notification(user, title, message, notification_type='info', related_model=None, related_id=None):
    """Create a notification for a user"""
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        related_model=related_model,
        related_id=related_id
    )
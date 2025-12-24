from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel
from django.utils import timezone

class Notification(TimeStampedModel):
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
        ('reminder', 'Reminder'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    action_url = models.URLField(blank=True)
    related_model = models.CharField(max_length=50, blank=True)  # e.g., 'production.Order'
    related_id = models.IntegerField(null=True, blank=True)
    priority = models.IntegerField(default=1)  # 1=Low, 5=High
    
    class Meta:
        ordering = ['-created_at', '-priority']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    low_stock_alerts = models.BooleanField(default=True)
    quality_alerts = models.BooleanField(default=True)
    production_alerts = models.BooleanField(default=True)
    purchase_order_alerts = models.BooleanField(default=True)
    attendance_alerts = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
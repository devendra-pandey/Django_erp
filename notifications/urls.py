from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications_list, name='list'),
    path('unread/', views.unread_notifications, name='unread'),
    path('mark-read/<int:pk>/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
    path('delete/<int:pk>/', views.delete_notification, name='delete'),
    path('clear-all/', views.clear_all_notifications, name='clear_all'),
    
    # Preferences
    path('preferences/', views.notification_preferences, name='preferences'),
    path('preferences/update/', views.update_preferences, name='update_preferences'),
    
    # Real-time endpoints
    # path('ws/notifications/', views.NotificationConsumer.as_asgi()),  # Comment out for now
    path('api/unread-count/', views.unread_notification_count, name='unread_count'),
    
    # Email notifications
    path('test-email/', views.test_email_notification, name='test_email'),
]
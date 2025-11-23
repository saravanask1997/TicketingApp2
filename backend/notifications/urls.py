from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('list/', views.notification_list, name='list'),
    path('unread/', views.unread_count, name='unread_count'),
    path('mark-read/<uuid:notification_id>/', views.mark_as_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_read'),
]
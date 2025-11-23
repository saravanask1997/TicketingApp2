from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Notification


@login_required
@require_http_methods(["GET"])
def notification_list(request):
    """Get list of notifications for the current user"""
    notifications = Notification.objects.filter(
        user=request.user
    ).select_related('ticket').order_by('-created_at')[:20]

    data = []
    for notification in notifications:
        notif_data = {
            'id': str(notification.id),
            'title': notification.title,
            'message': notification.message,
            'created_at': notification.created_at.isoformat(),
            'is_read': notification.is_read,
            'ticket_id': str(notification.ticket.id) if notification.ticket else None,
        }
        data.append(notif_data)

    return JsonResponse({'notifications': data})


@login_required
@require_http_methods(["GET"])
def unread_count(request):
    """Get unread notification count for the current user"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
@require_http_methods(["POST"])
def mark_as_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})


@login_required
@require_http_methods(["POST"])
def mark_all_as_read(request):
    """Mark all notifications as read for the current user"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})
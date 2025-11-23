from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Notification


@shared_task
def send_email_notification(notification_id):
    """Send email notification asynchronously"""
    try:
        notification = Notification.objects.get(id=notification_id)

        # Prepare email context
        context = {
            'notification': notification,
            'ticket': notification.ticket,
            'user': notification.user,
        }

        # Render email templates
        subject = f'[Ticketing System] {notification.title}'

        html_message = render_to_string('emails/notification_email.html', context)
        plain_message = render_to_string('emails/notification_email.txt', context)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.user.email],
            html_message=html_message,
            fail_silently=False,
        )

        # Mark notification as sent
        notification.mark_as_sent()

        return f"Email sent successfully to {notification.user.email}"

    except Notification.DoesNotExist:
        return f"Notification {notification_id} not found"
    except Exception as e:
        return f"Failed to send email: {str(e)}"


@shared_task
def send_ticket_created_notification(ticket_id):
    """Send notifications when a new ticket is created"""
    from tickets.models import Ticket
    from users.models import User

    try:
        ticket = Ticket.objects.get(id=ticket_id)

        # Get all admin and automation team users
        notify_users = User.objects.filter(role__in=['admin', 'automation_team'])

        for user in notify_users:
            if user != ticket.created_by:  # Don't notify the creator
                notification = Notification.create_notification(
                    user=user,
                    title=f'New Ticket: {ticket.title}',
                    message=f'A new ticket has been created by {ticket.created_by.get_full_name() or ticket.created_by.email}',
                    notification_type='both',
                    ticket=ticket
                )

                # Queue email sending
                send_email_notification.delay(str(notification.id))

        return f"Notifications sent for ticket {ticket.title}"

    except Ticket.DoesNotExist:
        return f"Ticket {ticket_id} not found"
    except Exception as e:
        return f"Failed to send ticket created notification: {str(e)}"


@shared_task
def send_status_update_notification(ticket_id, old_status, new_status, changed_by_id):
    """Send notifications when ticket status is updated"""
    from tickets.models import Ticket
    from users.models import User

    try:
        ticket = Ticket.objects.get(id=ticket_id)
        changed_by = User.objects.get(id=changed_by_id)

        # Notify ticket creator (if not the one who changed status)
        if ticket.created_by and ticket.created_by != changed_by:
            notification = Notification.create_notification(
                user=ticket.created_by,
                title=f'Status Update: {ticket.title}',
                message=f'Your ticket status has been updated from {old_status} to {new_status} by {changed_by.get_full_name() or changed_by.email}',
                notification_type='both',
                ticket=ticket
            )

            send_email_notification.delay(str(notification.id))

        return f"Status update notifications sent for ticket {ticket.title}"

    except (Ticket.DoesNotExist, User.DoesNotExist):
        return f"Ticket or user not found for ticket {ticket_id}"
    except Exception as e:
        return f"Failed to send status update notification: {str(e)}"
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('delivered', 'Delivered'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    CATEGORY_CHOICES = [
        ('automation', 'Automation Request'),
        ('bug_report', 'Bug Report'),
        ('feature_request', 'Feature Request'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tickets')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    attachments = models.JSONField(default=list, blank=True)  # Store file paths
    tags = models.JSONField(default=list, blank=True)  # Store tag strings

    class Meta:
        db_table = 'tickets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['category']),
            models.Index(fields=['created_by']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Set closed_at when status changes to closed
        if self.status == 'closed' and not self.closed_at:
            self.closed_at = timezone.now()
        elif self.status != 'closed' and self.closed_at:
            self.closed_at = None
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Check if ticket is overdue"""
        if self.due_date and self.status not in ['closed', 'delivered']:
            return timezone.now() > self.due_date
        return False

    @property
    def resolution_time(self):
        """Calculate resolution time in hours"""
        if self.closed_at and self.created_at:
            return (self.closed_at - self.created_at).total_seconds() / 3600
        return None

    def can_be_viewed_by(self, user):
        """Check if user can view this ticket"""
        if user.is_admin:
            return True
        if user.is_automation_team:
            return True
        return self.created_by == user

    def can_be_edited_by(self, user):
        """Check if user can edit this ticket"""
        if user.is_admin:
            return True
        if user.is_automation_team:
            return True
        return False

    def assign_to(self, user):
        """Assign ticket to a user"""
        self.assigned_to = user
        self.save()

    def change_status(self, new_status, changed_by, notes=''):
        """Change ticket status and create history record"""
        old_status = self.status
        if old_status != new_status:
            self.status = new_status
            self.save()
            TicketStatusHistory.objects.create(
                ticket=self,
                old_status=old_status,
                new_status=new_status,
                changed_by=changed_by,
                notes=notes
            )


class Comment(models.Model):
    COMMENT_TYPE_CHOICES = [
        ('public', 'Public Comment'),
        ('internal', 'Internal Note'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    comment_type = models.CharField(max_length=10, choices=COMMENT_TYPE_CHOICES, default='public')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Attachments for comments
    attachments = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'comments'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.ticket.title}"

    def can_be_viewed_by(self, user):
        """Check if user can view this comment"""
        if self.comment_type == 'internal':
            return user.is_admin or user.is_automation_team
        return self.ticket.can_be_viewed_by(user)


class TicketStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'ticket_status_history'
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.ticket.title}: {self.old_status} → {self.new_status}"
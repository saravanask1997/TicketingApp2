import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'General User'),
        ('admin', 'Administrator'),
        ('automation_team', 'Automation Team Member'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_automation_team(self):
        return self.role == 'automation_team'

    def can_view_ticket(self, ticket):
        """Check if user can view a specific ticket"""
        if self.is_admin:
            return True
        if self.is_automation_team:
            return True  # Can view all tickets as automation team
        return ticket.created_by == self

    def can_edit_ticket(self, ticket):
        """Check if user can edit a specific ticket"""
        if self.is_admin:
            return True
        if self.is_automation_team:
            return True  # Can edit tickets as automation team
        return False  # Regular users cannot edit tickets after creation
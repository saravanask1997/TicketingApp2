from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to admin users only"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin


class AutomationTeamRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to admin and automation team users"""

    def test_func(self):
        return self.request.user.is_authenticated and \
               self.request.user.role in ['admin', 'automation_team']


class TicketOwnerMixin(UserPassesTestMixin):
    """Mixin to restrict access to ticket owner and admin/automation team"""

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False

        if self.request.user.role in ['admin', 'automation_team']:
            return True

        # For regular users, check if they own the ticket
        ticket = self.get_object()
        return ticket.created_by == self.request.user
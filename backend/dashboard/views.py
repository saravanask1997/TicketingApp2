from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, TemplateView
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, DurationField, FloatField
from django.utils import timezone
from datetime import timedelta
from tickets.models import Ticket, TicketStatusHistory
from users.models import User


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_admin:
            # Admin dashboard - full system overview
            context.update(self.get_admin_context())
        elif user.is_automation_team:
            # Automation team dashboard - assigned tickets and team metrics
            context.update(self.get_automation_team_context())
        else:
            # Regular user dashboard - their tickets only
            context.update(self.get_user_context())

        return context

    def get_admin_context(self):
        """Context for admin dashboard"""
        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        # System overview
        total_tickets = Ticket.objects.count()
        open_tickets = Ticket.objects.filter(status='open').count()
        in_progress_tickets = Ticket.objects.filter(status='in_progress').count()
        closed_tickets = Ticket.objects.filter(status='closed').count()

        # Recent tickets
        recent_tickets = Ticket.objects.select_related('created_by', 'assigned_to').order_by('-created_at')[:10]

        # Ticket counts by status
        status_counts = Ticket.objects.values('status').annotate(count=Count('id'))

        # Ticket counts by priority
        priority_counts = Ticket.objects.values('priority').annotate(count=Count('id'))

        # Ticket counts by category
        category_counts = Ticket.objects.values('category').annotate(count=Count('id'))

        # Average resolution time (last 30 days)
        avg_resolution_time = self.get_average_resolution_time(30)

        # User performance metrics
        user_performance = self.get_user_performance_metrics()

        return {
            'dashboard_type': 'admin',
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'in_progress_tickets': in_progress_tickets,
            'closed_tickets': closed_tickets,
            'recent_tickets': recent_tickets,
            'status_counts': list(status_counts),
            'priority_counts': list(priority_counts),
            'category_counts': list(category_counts),
            'avg_resolution_time': avg_resolution_time,
            'user_performance': user_performance,
        }

    def get_automation_team_context(self):
        """Context for automation team dashboard"""
        user = self.request.user
        now = timezone.now()

        # Assigned tickets
        assigned_tickets = Ticket.objects.filter(assigned_to=user)
        my_open_tickets = assigned_tickets.filter(status='open').count()
        my_in_progress_tickets = assigned_tickets.filter(status='in_progress').count()
        my_closed_tickets = assigned_tickets.filter(status='closed').count()

        # Recent assigned tickets
        recent_assigned = assigned_tickets.select_related('created_by').order_by('-updated_at')[:10]

        # My tickets by status
        my_status_counts = assigned_tickets.values('status').annotate(count=Count('id'))

        # Overdue tickets assigned to me
        overdue_tickets = assigned_tickets.filter(
            due_date__lt=now,
            status__in=['open', 'in_progress']
        )

        return {
            'dashboard_type': 'automation_team',
            'my_open_tickets': my_open_tickets,
            'my_in_progress_tickets': my_in_progress_tickets,
            'my_closed_tickets': my_closed_tickets,
            'recent_assigned_tickets': recent_assigned,
            'my_status_counts': list(my_status_counts),
            'overdue_tickets_count': overdue_tickets.count(),
            'overdue_tickets': overdue_tickets[:5],
        }

    def get_user_context(self):
        """Context for regular user dashboard"""
        user = self.request.user

        # User's tickets
        user_tickets = Ticket.objects.filter(created_by=user)
        my_open_tickets = user_tickets.filter(status='open').count()
        my_in_progress_tickets = user_tickets.filter(status='in_progress').count()
        my_closed_tickets = user_tickets.filter(status='closed').count()

        # Recent tickets
        recent_tickets = user_tickets.select_related('assigned_to').order_by('-created_at')[:10]

        # My tickets by status
        my_status_counts = user_tickets.values('status').annotate(count=Count('id'))

        return {
            'dashboard_type': 'user',
            'my_open_tickets': my_open_tickets,
            'my_in_progress_tickets': my_in_progress_tickets,
            'my_closed_tickets': my_closed_tickets,
            'recent_tickets': recent_tickets,
            'my_status_counts': list(my_status_counts),
        }

    def get_average_resolution_time(self, days=30):
        """Calculate average resolution time in hours"""
        cutoff_date = timezone.now() - timedelta(days=days)

        tickets = Ticket.objects.filter(
            status='closed',
            closed_at__gte=cutoff_date
        ).annotate(
            resolution_time=ExpressionWrapper(
                F('closed_at') - F('created_at'),
                output_field=DurationField()
            )
        ).aggregate(
            avg_resolution=Avg('resolution_time')
        )

        if tickets['avg_resolution']:
            return tickets['avg_resolution'].total_seconds() / 3600  # Convert to hours
        return 0

    def get_user_performance_metrics(self):
        """Get performance metrics for automation team members"""
        return User.objects.filter(
            role='automation_team'
        ).annotate(
            tickets_assigned=Count('assigned_tickets'),
            tickets_closed=Count('assigned_tickets', filter=Q(assigned_tickets__status='closed'))
        ).annotate(
            closure_rate=ExpressionWrapper(
                F('tickets_closed') * 100.0 / F('tickets_assigned'),
                output_field=FloatField()
            )
        ).order_by('-closure_rate')


class AnalyticsView(AdminRequiredMixin, TemplateView):
    template_name = 'dashboard/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get time period filter
        days = int(self.request.GET.get('days', 30))
        cutoff_date = timezone.now() - timedelta(days=days)

        # Ticket trends over time
        ticket_trends = self.get_ticket_trends(cutoff_date)

        # Resolution time by category
        resolution_by_category = self.get_resolution_time_by_category(cutoff_date)

        # Team performance
        team_performance = self.get_team_performance(cutoff_date)

        # Priority analysis
        priority_analysis = self.get_priority_analysis(cutoff_date)

        context.update({
            'days': days,
            'ticket_trends': ticket_trends,
            'resolution_by_category': resolution_by_category,
            'team_performance': team_performance,
            'priority_analysis': priority_analysis,
        })

        return context

    def get_ticket_trends(self, cutoff_date):
        """Get ticket creation trends over time"""
        from django.db.models import TruncDate

        return Ticket.objects.filter(
            created_at__gte=cutoff_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

    def get_resolution_time_by_category(self, cutoff_date):
        """Get average resolution time by category"""
        return Ticket.objects.filter(
            status='closed',
            closed_at__gte=cutoff_date
        ).annotate(
            resolution_time_hours=ExpressionWrapper(
                (F('closed_at') - F('created_at')) * 24,
                output_field=FloatField()
            )
        ).values('category').annotate(
            avg_resolution=Avg('resolution_time_hours'),
            count=Count('id')
        ).order_by('-avg_resolution')

    def get_team_performance(self, cutoff_date):
        """Get detailed team performance metrics"""
        return User.objects.filter(
            role='automation_team'
        ).annotate(
            tickets_assigned=Count('assigned_tickets', filter=Q(assigned_tickets__created_at__gte=cutoff_date)),
            tickets_closed=Count('assigned_tickets', filter=Q(assigned_tickets__status='closed', assigned_tickets__closed_at__gte=cutoff_date))
        ).annotate(
            closure_rate=ExpressionWrapper(
                F('tickets_closed') * 100.0 / F('tickets_assigned'),
                output_field=FloatField()
            )
        ).order_by('-tickets_closed')

    def get_priority_analysis(self, cutoff_date):
        """Get analysis of tickets by priority"""
        return Ticket.objects.filter(
            created_at__gte=cutoff_date
        ).values('priority').annotate(
            total=Count('id'),
            closed=Count('id', filter=Q(status='closed')),
            avg_resolution_time=Avg(
                ExpressionWrapper(
                    (F('closed_at') - F('created_at')) * 24,
                    output_field=FloatField()
                ),
                filter=Q(status='closed')
            )
        ).order_by('priority')


class UserManagementView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'dashboard/user_management.html'
    context_object_name = 'users'
    paginate_by = 50

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')

        # Apply filters
        role_filter = self.request.GET.get('role')
        status_filter = self.request.GET.get('status')
        search_query = self.request.GET.get('search')

        if role_filter:
            queryset = queryset.filter(role=role_filter)
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_choices'] = User.ROLE_CHOICES

        # Preserve filter parameters
        context['current_filters'] = {
            'role': self.request.GET.get('role', ''),
            'status': self.request.GET.get('status', ''),
            'search': self.request.GET.get('search', ''),
        }

        return context
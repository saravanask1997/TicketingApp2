from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from users.mixins import AdminRequiredMixin, AutomationTeamRequiredMixin, TicketOwnerMixin
from .models import Ticket, Comment, TicketStatusHistory
from .forms import (
    TicketForm, TicketUpdateForm, TicketAssignmentForm,
    TicketStatusForm, CommentForm
)


class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.select_related('created_by', 'assigned_to')

        # Filter based on user role
        if user.is_admin or user.is_automation_team:
            # Admin and automation team can see all tickets
            pass
        else:
            # Regular users only see their own tickets
            queryset = queryset.filter(created_by=user)

        # Apply filters
        status_filter = self.request.GET.get('status')
        priority_filter = self.request.GET.get('priority')
        category_filter = self.request.GET.get('category')
        assigned_filter = self.request.GET.get('assigned_to')
        search_query = self.request.GET.get('search')

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        if category_filter:
            queryset = queryset.filter(category=category_filter)
        if assigned_filter:
            queryset = queryset.filter(assigned_to__id=assigned_filter)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Ticket.STATUS_CHOICES
        context['priority_choices'] = Ticket.PRIORITY_CHOICES
        context['category_choices'] = Ticket.CATEGORY_CHOICES

        # Add assigned users filter for admin/automation team
        if self.request.user.is_admin or self.request.user.is_automation_team:
            from users.models import User
            context['assigned_users'] = User.objects.filter(
                role__in=['admin', 'automation_team']
            )

        # Preserve filter parameters
        context['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'priority': self.request.GET.get('priority', ''),
            'category': self.request.GET.get('category', ''),
            'assigned_to': self.request.GET.get('assigned_to', ''),
            'search': self.request.GET.get('search', ''),
        }

        return context


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'tickets/ticket_form.html'
    success_url = reverse_lazy('tickets:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        # Create notification for admins/automation team
        from notifications.models import Notification
        from users.models import User

        # Notify all admin and automation team users
        notify_users = User.objects.filter(role__in=['admin', 'automation_team'])
        for user in notify_users:
            Notification.objects.create(
                user=user,
                title=f'New Ticket: {form.instance.title}',
                message=f'A new ticket has been created by {self.request.user.get_full_name() or self.request.user.email}',
                ticket=form.instance,
                notification_type='both'
            )

        messages.success(self.request, 'Ticket created successfully!')
        return response


class TicketDetailView(TicketOwnerMixin, DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = self.get_object()

        # Get comments
        comments = ticket.comments.filter(
            comment_type='public'
        ) if not (self.request.user.is_admin or self.request.user.is_automation_team) else ticket.comments.all()

        context['comments'] = comments.select_related('author').order_by('created_at')
        context['status_history'] = ticket.status_history.select_related('changed_by').order_by('-changed_at')

        # Add forms
        if ticket.can_be_edited_by(self.request.user):
            context['assignment_form'] = TicketAssignmentForm(instance=ticket)
            context['status_form'] = TicketStatusForm(instance=ticket)

        context['comment_form'] = CommentForm(user=self.request.user)

        return context


class TicketUpdateView(AdminRequiredMixin, UpdateView):
    model = Ticket
    form_class = TicketUpdateForm
    template_name = 'tickets/ticket_form.html'
    success_url = reverse_lazy('tickets:list')

    def form_valid(self, form):
        old_status = Ticket.objects.get(pk=self.object.pk).status
        new_status = form.cleaned_data.get('status')

        response = super().form_valid(form)

        # Create status history if changed
        if old_status != new_status:
            TicketStatusHistory.objects.create(
                ticket=self.object,
                old_status=old_status,
                new_status=new_status,
                changed_by=self.request.user
            )

            # Notify ticket creator about status change
            if self.object.created_by and self.object.created_by != self.request.user:
                from notifications.models import Notification
                Notification.objects.create(
                    user=self.object.created_by,
                    title=f'Status Update: {self.object.title}',
                    message=f'Your ticket status has been updated from {old_status} to {new_status}',
                    ticket=self.object,
                    notification_type='both'
                )

        # Notify about assignment if changed
        old_assigned = Ticket.objects.get(pk=self.object.pk).assigned_to
        new_assigned = form.cleaned_data.get('assigned_to')

        if old_assigned != new_assigned and new_assigned:
            from notifications.models import Notification
            Notification.objects.create(
                user=new_assigned,
                title=f'Ticket Assigned: {self.object.title}',
                message=f'You have been assigned to this ticket',
                ticket=self.object,
                notification_type='both'
            )

        messages.success(self.request, 'Ticket updated successfully!')
        return response


@login_required
def assign_ticket(request, ticket_id):
    """Assign ticket to a user"""
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if not ticket.can_be_edited_by(request.user):
        messages.error(request, 'You do not have permission to assign this ticket.')
        return redirect('tickets:detail', pk=ticket_id)

    if request.method == 'POST':
        form = TicketAssignmentForm(request.POST, instance=ticket)
        if form.is_valid():
            old_assigned = ticket.assigned_to
            form.save()

            # Create notification if assigned to someone new
            new_assigned = ticket.assigned_to
            if new_assigned and old_assigned != new_assigned:
                from notifications.models import Notification
                Notification.objects.create(
                    user=new_assigned,
                    title=f'Ticket Assigned: {ticket.title}',
                    message=f'You have been assigned to this ticket by {request.user.get_full_name() or request.user.email}',
                    ticket=ticket,
                    notification_type='both'
                )

            messages.success(request, f'Ticket assigned to {new_assigned.get_full_name() if new_assigned else "Unassigned"}')

    return redirect('tickets:detail', pk=ticket_id)


@login_required
def update_status(request, ticket_id):
    """Update ticket status"""
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if not ticket.can_be_edited_by(request.user):
        messages.error(request, 'You do not have permission to update this ticket status.')
        return redirect('tickets:detail', pk=ticket_id)

    if request.method == 'POST':
        form = TicketStatusForm(request.POST, instance=ticket)
        if form.is_valid():
            old_status = ticket.status
            new_status = form.cleaned_data['status']
            notes = form.cleaned_data.get('status_notes', '')

            ticket.change_status(new_status, request.user, notes)

            # Notify ticket creator about status change
            if ticket.created_by and ticket.created_by != request.user:
                from notifications.models import Notification
                Notification.objects.create(
                    user=ticket.created_by,
                    title=f'Status Update: {ticket.title}',
                    message=f'Your ticket status has been updated from {old_status} to {new_status}',
                    ticket=ticket,
                    notification_type='both'
                )

            messages.success(request, f'Ticket status updated to {ticket.get_status_display()}')

    return redirect('tickets:detail', pk=ticket_id)


@login_required
def add_comment(request, ticket_id):
    """Add comment to ticket"""
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if not ticket.can_be_viewed_by(request.user):
        messages.error(request, 'You do not have permission to view this ticket.')
        return redirect('tickets:list')

    if request.method == 'POST':
        form = CommentForm(request.POST, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()

            # Notify other participants
            from notifications.models import Notification
            participants = []

            # Notify ticket creator
            if ticket.created_by and ticket.created_by != request.user:
                participants.append(ticket.created_by)

            # Notify assigned user
            if ticket.assigned_to and ticket.assigned_to != request.user:
                participants.append(ticket.assigned_to)

            # Notify admin/automation team for internal comments
            if comment.comment_type == 'internal':
                from users.models import User
                team_members = User.objects.filter(
                    role__in=['admin', 'automation_team']
                ).exclude(id=request.user.id)
                participants.extend(team_members)

            for participant in participants:
                Notification.objects.create(
                    user=participant,
                    title=f'New Comment on: {ticket.title}',
                    message=f'{request.user.get_full_name() or request.user.email} added a {"comment" if comment.comment_type == "public" else "internal note"}',
                    ticket=ticket,
                    notification_type='onscreen' if comment.comment_type == 'internal' else 'both'
                )

            messages.success(request, 'Comment added successfully!')

    return redirect('tickets:detail', pk=ticket_id)


class MyTicketsView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/my_tickets.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        return Ticket.objects.filter(
            created_by=self.request.user
        ).select_related('assigned_to').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Ticket.STATUS_CHOICES
        context['priority_choices'] = Ticket.PRIORITY_CHOICES
        return context
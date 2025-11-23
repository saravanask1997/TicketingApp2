from django.contrib import admin
from .models import Ticket, Comment, TicketStatusHistory


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'assigned_to', 'status', 'priority', 'category', 'created_at', 'is_overdue')
    list_filter = ('status', 'priority', 'category', 'created_at', 'assigned_to')
    search_fields = ('title', 'description', 'created_by__email', 'created_by__first_name', 'created_by__last_name')
    list_editable = ('status', 'priority', 'assigned_to')
    readonly_fields = ('id', 'created_at', 'updated_at', 'closed_at', 'resolution_time')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'priority')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'assigned_to', 'due_date')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at', 'closed_at', 'resolution_time', 'attachments', 'tags'),
            'classes': ('collapse',)
        }),
    )

    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'assigned_to')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'comment_type', 'created_at')
    list_filter = ('comment_type', 'created_at', 'ticket__status')
    search_fields = ('content', 'ticket__title', 'author__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ticket', 'author')


@admin.register(TicketStatusHistory)
class TicketStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('new_status', 'old_status', 'changed_at')
    search_fields = ('ticket__title', 'changed_by__email', 'notes')
    readonly_fields = ('id', 'changed_at')
    date_hierarchy = 'changed_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ticket', 'changed_by')
from django import forms
from .models import Ticket, Comment
from users.models import User


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ticket title',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your automation request in detail',
                'required': True
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 10:
            raise forms.ValidationError("Title must be at least 10 characters long")
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 20:
            raise forms.ValidationError("Description must be at least 20 characters long")
        return description


class TicketUpdateForm(forms.ModelForm):
    """Form for admins/automation team to update tickets"""
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority', 'status', 'assigned_to', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users to only automation team members for assignment
        self.fields['assigned_to'].queryset = User.objects.filter(
            role__in=['admin', 'automation_team']
        )
        self.fields['assigned_to'].required = False


class TicketAssignmentForm(forms.ModelForm):
    """Form specifically for assigning tickets"""
    class Meta:
        model = Ticket
        fields = ['assigned_to']
        widgets = {
            'assigned_to': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users to only automation team members
        self.fields['assigned_to'].queryset = User.objects.filter(
            role__in=['admin', 'automation_team']
        )
        self.fields['assigned_to'].required = False


class TicketStatusForm(forms.ModelForm):
    """Form for updating ticket status with notes"""
    status_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add notes about this status change (optional)'
        }),
        required=False
    )

    class Meta:
        model = Ticket
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'comment_type']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add your comment...',
                'required': True
            }),
            'comment_type': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Only show internal note option for admin/automation team
        if self.user and not (self.user.is_admin or self.user.is_automation_team):
            self.fields['comment_type'].widget = forms.HiddenInput()
            self.fields['comment_type'].initial = 'public'
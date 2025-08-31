from django import forms
from .models import ContactMessage, ContactReply


class ContactForm(forms.ModelForm):
    """Contact form for website visitors"""
    
    class Meta:
        model = ContactMessage
        fields = [
            'name', 'email', 'phone', 'company', 'website',
            'subject', 'subject_custom', 'message',
            'project_budget', 'project_timeline'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your company name (optional)'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourwebsite.com'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-control'
            }),
            'subject_custom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Please specify your subject',
                'style': 'display: none;'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Tell us about your project or inquiry...'
            }),
            'project_budget': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., $5,000 - $10,000'
            }),
            'project_timeline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2-3 months'
            }),
        }
        
        labels = {
            'name': 'Full Name',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'company': 'Company',
            'website': 'Website',
            'subject': 'Subject',
            'subject_custom': 'Custom Subject',
            'message': 'Message',
            'project_budget': 'Project Budget (Optional)',
            'project_timeline': 'Project Timeline (Optional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['email'].required = True
        self.fields['message'].required = True
        
        # Add required asterisk to labels
        for field_name, field in self.fields.items():
            if field.required:
                field.label += ' *'


class QuickContactForm(forms.Form):
    """Simplified contact form for quick inquiries"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Your message'
        })
    )


class ContactReplyForm(forms.ModelForm):
    """Form for admin to reply to contact messages"""
    
    class Meta:
        model = ContactReply
        fields = ['subject', 'message']
        
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Reply subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Your reply message...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].required = True
        self.fields['message'].required = True

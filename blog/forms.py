from django import forms
from .models import Comment, Newsletter


class CommentForm(forms.ModelForm):
    """Form for adding comments to blog posts"""
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Write your comment here...'
        }),
        label='Comment'
    )
    
    class Meta:
        model = Comment
        fields = ['content']


class NewsletterForm(forms.ModelForm):
    """Form for newsletter subscription"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name (optional)'
        })
    )
    
    class Meta:
        model = Newsletter
        fields = ['email', 'name']

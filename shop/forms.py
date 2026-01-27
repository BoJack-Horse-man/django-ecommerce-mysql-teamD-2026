"""
Django Forms for E-Commerce Application

Forms handle user input validation and rendering.
Each form corresponds to a model or specific use case.

Why use ModelForm? Automatically generates form fields from model,
handles validation, and can save directly to database.
"""

from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import UserProfile, ProductReview, NewsletterSubscriber


class UserProfileForm(forms.ModelForm):
    """
    Form for updating user profile information.
    
    Why ModelForm? Automatically handles field validation and saving.
    Only includes 'photo' field - other fields can be added as needed.
    """
    class Meta:
        model = UserProfile
        fields = ['photo', 'phone', 'address']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Your address'
            }),
        }


class ReviewForm(forms.ModelForm):
    """
    Form for submitting product reviews.
    
    Why custom validation? Ensure rating is between 1-5 and review is meaningful.
    """
    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'type': 'number'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Review title',
                'maxlength': 200
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Write your review here...'
            }),
        }
    
    def clean_rating(self):
        """Validate rating is between 1 and 5."""
        rating = self.cleaned_data.get('rating')
        if rating and (rating < 1 or rating > 5):
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating
    
    def clean_comment(self):
        """Ensure comment has meaningful content."""
        comment = self.cleaned_data.get('comment')
        if comment and len(comment.strip()) < 10:
            raise forms.ValidationError("Please provide a more detailed review (at least 10 characters).")
        return comment


class ContactForm(forms.Form):
    """
    Contact form for customer inquiries.
    
    Why Form instead of ModelForm? We don't need to store contact submissions
    in database (though you could add a ContactSubmission model if needed).
    """
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name',
            'required': True
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com',
            'required': True
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject',
            'required': True
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Your message...',
            'required': True
        })
    )
    
    def clean_message(self):
        """Ensure message has meaningful content."""
        message = self.cleaned_data.get('message')
        if message and len(message.strip()) < 10:
            raise forms.ValidationError("Please provide a more detailed message (at least 10 characters).")
        return message


class NewsletterForm(forms.ModelForm):
    """
    Newsletter subscription form.
    
    Simple form with just email field for subscription.
    """
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'required': True
            })
        }
    
    def clean_email(self):
        """Normalize email to lowercase."""
        email = self.cleaned_data.get('email')
        if email:
            return email.lower().strip()
        return email

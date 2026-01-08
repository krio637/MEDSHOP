from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import re
from .models import UserProfile, SiteSettings, ContactMessage

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
        # Add placeholders
        self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last name'
        self.fields['email'].widget.attrs['placeholder'] = 'Email address'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
        # Add placeholders
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last name'
        self.fields['email'].widget.attrs['placeholder'] = 'Email address'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Phone number'
        self.fields['address'].widget.attrs['placeholder'] = 'Your address'
        
        # Pre-populate profile fields if user has a profile
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['phone_number'].initial = self.instance.profile.phone_number
            self.fields['address'].initial = self.instance.profile.address
            self.fields['date_of_birth'].initial = self.instance.profile.date_of_birth
    
    def save(self, commit=True):
        user = super().save(commit)
        if commit:
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone_number = self.cleaned_data['phone_number']
            profile.address = self.cleaned_data['address']
            profile.date_of_birth = self.cleaned_data['date_of_birth']
            profile.save()
        return user

class SocialSettingsForm(forms.ModelForm):
    """Form for managing social media links and settings"""
    
    class Meta:
        model = SiteSettings
        fields = ['facebook_url', 'instagram_url', 'youtube_url', 'twitter_url', 'linkedin_url', 'whatsapp_number']
        widgets = {
            'facebook_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/yourpage'
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://instagram.com/youraccount'
            }),
            'youtube_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/yourchannel'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/youraccount'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/company/yourcompany'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91XXXXXXXXXX'
            })
        }
        labels = {
            'facebook_url': 'Facebook Page URL',
            'instagram_url': 'Instagram Profile URL',
            'youtube_url': 'YouTube Channel URL',
            'twitter_url': 'Twitter Profile URL',
            'linkedin_url': 'LinkedIn Profile URL',
            'whatsapp_number': 'WhatsApp Number'
        }
        help_texts = {
            'facebook_url': 'Enter your Facebook page URL (optional)',
            'instagram_url': 'Enter your Instagram profile URL (optional)',
            'youtube_url': 'Enter your YouTube channel URL (optional)',
            'twitter_url': 'Enter your Twitter profile URL (optional)',
            'linkedin_url': 'Enter your LinkedIn profile URL (optional)',
            'whatsapp_number': 'Enter WhatsApp number with country code, e.g., +91XXXXXXXXXX (optional)'
        }
    
    def clean_facebook_url(self):
        """Validate and normalize Facebook URL"""
        url = self.cleaned_data.get('facebook_url')
        if url:
            return self._validate_and_normalize_url(url, 'facebook.com')
        return url
    
    def clean_instagram_url(self):
        """Validate and normalize Instagram URL"""
        url = self.cleaned_data.get('instagram_url')
        if url:
            return self._validate_and_normalize_url(url, 'instagram.com')
        return url
    
    def clean_youtube_url(self):
        """Validate and normalize YouTube URL"""
        url = self.cleaned_data.get('youtube_url')
        if url:
            return self._validate_and_normalize_url(url, 'youtube.com')
        return url
    
    def clean_twitter_url(self):
        """Validate and normalize Twitter URL"""
        url = self.cleaned_data.get('twitter_url')
        if url:
            return self._validate_and_normalize_url(url, 'twitter.com')
        return url
    
    def clean_linkedin_url(self):
        """Validate and normalize LinkedIn URL"""
        url = self.cleaned_data.get('linkedin_url')
        if url:
            return self._validate_and_normalize_url(url, 'linkedin.com')
        return url
    
    def clean_whatsapp_number(self):
        """Validate WhatsApp number format"""
        number = self.cleaned_data.get('whatsapp_number')
        if number:
            # Remove spaces and special characters except +
            cleaned_number = re.sub(r'[^\d+]', '', number)
            
            # Check if it starts with + and has 10-15 digits
            if not re.match(r'^\+\d{10,15}$', cleaned_number):
                raise ValidationError(
                    'WhatsApp number must be in format +CCXXXXXXXXXX (country code + phone number)'
                )
            return cleaned_number
        return number
    
    def _validate_and_normalize_url(self, url, expected_domain):
        """Validate URL format and normalize protocol"""
        if not url:
            return url
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Validate URL format
        validator = URLValidator()
        try:
            validator(url)
        except ValidationError:
            raise ValidationError(f'Please enter a valid URL for {expected_domain}')
        
        # Check if URL contains expected domain (optional validation)
        if expected_domain not in url.lower():
            raise ValidationError(f'URL should be for {expected_domain}')
        
        # Ensure https protocol for security
        if url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)
        
        return url

class ContactForm(forms.ModelForm):
    """Form for public contact submissions"""
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com',
                'required': True
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject of your message',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your message here...',
                'rows': 5,
                'required': True
            })
        }
        labels = {
            'name': 'Full Name',
            'email': 'Email Address',
            'subject': 'Subject',
            'message': 'Message'
        }
    
    def clean_name(self):
        """Validate name field"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise ValidationError('Name must be at least 2 characters long')
            if len(name) > 100:
                raise ValidationError('Name cannot exceed 100 characters')
            # Check for basic name validation (letters, spaces, hyphens, apostrophes)
            if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
                raise ValidationError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return name
    
    def clean_subject(self):
        """Validate subject field"""
        subject = self.cleaned_data.get('subject')
        if subject:
            subject = subject.strip()
            if len(subject) < 3:
                raise ValidationError('Subject must be at least 3 characters long')
            if len(subject) > 200:
                raise ValidationError('Subject cannot exceed 200 characters')
        return subject
    
    def clean_message(self):
        """Validate message field"""
        message = self.cleaned_data.get('message')
        if message:
            message = message.strip()
            if len(message) < 10:
                raise ValidationError('Message must be at least 10 characters long')
            if len(message) > 5000:
                raise ValidationError('Message cannot exceed 5000 characters')
            # Check for empty or whitespace-only message
            if not message or message.isspace():
                raise ValidationError('Message cannot be empty or contain only whitespace')
        return message
    
    def clean_email(self):
        """Additional email validation"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            # Additional validation can be added here if needed
        return email
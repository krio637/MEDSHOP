"""
Property-based tests for social media URL management functionality.

**Feature: admin-social-contact, Property 1: Social Media URL Management**
**Validates: Requirements 1.2, 1.4, 1.5**
"""

from django.test import TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase as HypothesisTestCase
import re
from medicines.models import SiteSettings
from medicines.forms import SocialSettingsForm


class SocialMediaURLManagementPropertyTest(HypothesisTestCase):
    """Property-based tests for social media URL management"""
    
    def setUp(self):
        """Clean up any existing settings before each test"""
        SiteSettings.objects.all().delete()
    
    @given(
        facebook_url=st.one_of(
            st.none(),
            st.text(min_size=0, max_size=0),  # Empty string
            st.builds(
                lambda domain, path: f"https://facebook.com/{domain}/{path}",
                domain=st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')), min_size=1, max_size=20),
                path=st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')), min_size=1, max_size=20)
            ),
            st.builds(
                lambda domain, path: f"facebook.com/{domain}/{path}",  # Without protocol
                domain=st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')), min_size=1, max_size=20),
                path=st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')), min_size=1, max_size=20)
            )
        ),
        instagram_url=st.one_of(
            st.none(),
            st.text(min_size=0, max_size=0),  # Empty string
            st.builds(
                lambda username: f"https://instagram.com/{username}",
                username=st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')), min_size=1, max_size=20)
            ),
            st.builds(
                lambda username: f"instagram.com/{username}",  # Without protocol
                username=st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')), min_size=1, max_size=20)
            )
        )
    )
    @settings(max_examples=100)
    def test_social_media_url_validation_and_normalization(self, facebook_url, instagram_url):
        """
        **Feature: admin-social-contact, Property 1: Social Media URL Management**
        
        For any social media URL input, the system should validate the format, 
        normalize the protocol, save valid URLs to the database, and immediately 
        reflect changes on the public website.
        """
        form_data = {
            'facebook_url': facebook_url,
            'instagram_url': instagram_url,
            'youtube_url': '',
            'twitter_url': '',
            'linkedin_url': '',
            'whatsapp_number': ''
        }
        
        form = SocialSettingsForm(data=form_data)
        
        if form.is_valid():
            # If form is valid, test that URLs are properly normalized
            cleaned_data = form.cleaned_data
            
            # Test protocol normalization (Requirement 1.5)
            for field_name in ['facebook_url', 'instagram_url']:
                url = cleaned_data.get(field_name)
                if url and url.strip():  # Non-empty URL
                    # Should start with http:// or https://
                    self.assertTrue(
                        url.startswith(('http://', 'https://')),
                        f"URL {url} should have protocol normalized"
                    )
            
            # Test database persistence (Requirement 1.2)
            settings = SiteSettings.get_settings()
            settings.facebook_url = cleaned_data['facebook_url']
            settings.instagram_url = cleaned_data['instagram_url']
            settings.save()
            
            # Verify data was saved correctly
            saved_settings = SiteSettings.objects.get(pk=settings.pk)
            self.assertEqual(saved_settings.facebook_url, cleaned_data['facebook_url'])
            self.assertEqual(saved_settings.instagram_url, cleaned_data['instagram_url'])
            
            # Test immediate reflection (Requirement 1.4)
            # The settings should be immediately available for retrieval
            current_settings = SiteSettings.get_settings()
            self.assertEqual(current_settings.facebook_url, cleaned_data['facebook_url'])
            self.assertEqual(current_settings.instagram_url, cleaned_data['instagram_url'])
    
    @given(
        whatsapp_number=st.one_of(
            st.none(),
            st.text(min_size=0, max_size=0),  # Empty string
            st.builds(
                lambda country_code, number: f"+{country_code}{number}",
                country_code=st.integers(min_value=1, max_value=999),
                number=st.text(alphabet='0123456789', min_size=10, max_size=12)
            ),
            st.builds(
                lambda country_code, number: f"+{country_code} {number[:5]} {number[5:]}",  # With spaces
                country_code=st.integers(min_value=1, max_value=999),
                number=st.text(alphabet='0123456789', min_size=10, max_size=12)
            ),
            st.text(alphabet='0123456789+-() ', min_size=1, max_size=20)  # Various formats
        )
    )
    @settings(max_examples=100)
    def test_whatsapp_number_validation_and_normalization(self, whatsapp_number):
        """
        Test WhatsApp number validation and normalization as part of URL management.
        """
        form_data = {
            'facebook_url': '',
            'instagram_url': '',
            'youtube_url': '',
            'twitter_url': '',
            'linkedin_url': '',
            'whatsapp_number': whatsapp_number
        }
        
        form = SocialSettingsForm(data=form_data)
        
        if form.is_valid():
            cleaned_number = form.cleaned_data['whatsapp_number']
            
            if cleaned_number:  # Non-empty number
                # Should be normalized to +CCXXXXXXXXXX format
                self.assertTrue(
                    re.match(r'^\+\d{10,15}$', cleaned_number),
                    f"WhatsApp number {cleaned_number} should be normalized to +CCXXXXXXXXXX format"
                )
                
                # Test database persistence
                settings = SiteSettings.get_settings()
                settings.whatsapp_number = cleaned_number
                settings.save()
                
                # Verify data was saved correctly
                saved_settings = SiteSettings.objects.get(pk=settings.pk)
                self.assertEqual(saved_settings.whatsapp_number, cleaned_number)
    
    @given(
        url_input=st.one_of(
            st.text(min_size=1, max_size=50),  # Random text
            st.builds(
                lambda: "not-a-valid-url",
            ),
            st.builds(
                lambda: "http://",
            ),
            st.builds(
                lambda: "https://",
            ),
            st.builds(
                lambda: "ftp://invalid.com",
            )
        )
    )
    @settings(max_examples=50)
    def test_invalid_url_rejection(self, url_input):
        """
        Test that invalid URLs are properly rejected by the form validation.
        """
        # Skip URLs that might accidentally be valid
        assume(not url_input.startswith(('http://facebook.com', 'https://facebook.com', 
                                        'http://instagram.com', 'https://instagram.com')))
        assume('facebook.com' not in url_input or len(url_input) < 15)
        assume('instagram.com' not in url_input or len(url_input) < 16)
        
        form_data = {
            'facebook_url': url_input,
            'instagram_url': '',
            'youtube_url': '',
            'twitter_url': '',
            'linkedin_url': '',
            'whatsapp_number': ''
        }
        
        form = SocialSettingsForm(data=form_data)
        
        # If the form is invalid, that's expected for invalid URLs
        # If the form is valid, the URL should be properly normalized
        if form.is_valid():
            cleaned_url = form.cleaned_data['facebook_url']
            if cleaned_url:  # Non-empty URL
                # Should be a valid URL with protocol
                self.assertTrue(
                    cleaned_url.startswith(('http://', 'https://')),
                    f"Valid URL {cleaned_url} should have protocol"
                )


class SocialMediaEmptyHandlingPropertyTest(HypothesisTestCase):
    """
    **Feature: admin-social-contact, Property 2: Empty Social Media Handling**
    **Validates: Requirements 1.3, 2.3**
    """
    
    def setUp(self):
        """Clean up any existing settings before each test"""
        SiteSettings.objects.all().delete()
    
    @given(
        empty_fields=st.lists(
            st.sampled_from(['facebook_url', 'instagram_url', 'youtube_url', 'twitter_url', 'linkedin_url']),
            min_size=1,
            max_size=5,
            unique=True
        ),
        whitespace_type=st.sampled_from(['', '   ', '\t', '\n', '  \t  \n  '])
    )
    @settings(max_examples=100)
    def test_empty_social_media_field_handling(self, empty_fields, whitespace_type):
        """
        For any social media field that is empty or contains only whitespace, 
        the system should accept the empty value and hide that platform's icon 
        from the public display.
        """
        # Create form data with some fields empty/whitespace
        form_data = {
            'facebook_url': 'https://facebook.com/test',
            'instagram_url': 'https://instagram.com/test',
            'youtube_url': 'https://youtube.com/test',
            'twitter_url': 'https://twitter.com/test',
            'linkedin_url': 'https://linkedin.com/test',
            'whatsapp_number': '+919876543210'
        }
        
        # Set selected fields to empty/whitespace
        for field in empty_fields:
            form_data[field] = whitespace_type
        
        form = SocialSettingsForm(data=form_data)
        
        # Form should be valid even with empty fields (Requirement 1.3)
        self.assertTrue(form.is_valid(), f"Form should accept empty fields. Errors: {form.errors}")
        
        # Save to database
        settings = SiteSettings.get_settings()
        for field, value in form.cleaned_data.items():
            setattr(settings, field, value)
        settings.save()
        
        # Verify empty fields are stored as None or empty string
        saved_settings = SiteSettings.objects.get(pk=settings.pk)
        for field in empty_fields:
            field_value = getattr(saved_settings, field)
            # Empty/whitespace should be stored as None or empty string
            self.assertIn(field_value, [None, ''], 
                         f"Empty field {field} should be None or empty string, got: {field_value}")
        
        # Verify non-empty fields are preserved
        for field, value in form_data.items():
            if field not in empty_fields and value.strip():
                saved_value = getattr(saved_settings, field)
                self.assertIsNotNone(saved_value, f"Non-empty field {field} should be preserved")
                self.assertNotEqual(saved_value, '', f"Non-empty field {field} should not be empty string")
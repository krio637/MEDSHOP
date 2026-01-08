"""
Property-based tests for medicine form processing
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from hypothesis import given, strategies as st, settings
from medicines.models import Medicine, Category
import string


class MedicineFormPropertyTests(TestCase):
    """Property-based tests for medicine form handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category for property testing'
        )
        
        self.client = Client()
        self.client.login(username='testadmin', password='testpass123')
    
    def tearDown(self):
        """Clean up after tests"""
        Medicine.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()
    
    def get_base_form_data(self, name_suffix=""):
        """Get base form data for medicine creation"""
        return {
            'name': f'Test Medicine {name_suffix}',
            'category': self.category.id,
            'description': 'Test medicine description',
            'mrp': '100.00',
            'price': '90.00',
            'stock_quantity': '50',
            'prescription_type': 'OTC',
            'expiry_date': '',
            'is_active': 'on'
        }
    
    @given(st.integers(min_value=1, max_value=1000))
    @settings(max_examples=100)
    def test_empty_manufacturer_field_handling(self, test_id):
        """
        **Feature: admin-medicine-form-fix, Property 1: Empty manufacturer field handling**
        
        For any valid medicine form data with an empty manufacturer field, 
        the form processing should save the medicine successfully with manufacturer set to None
        """
        form_data = self.get_base_form_data(f"empty_mfg_{test_id}")
        form_data['manufacturer'] = ''  # Empty manufacturer
        
        response = self.client.post(reverse('admin_medicine_add'), form_data)
        
        # Verify medicine was created successfully
        medicine = Medicine.objects.filter(name=form_data['name']).first()
        self.assertIsNotNone(medicine, "Medicine should be created with empty manufacturer")
        self.assertIsNone(medicine.manufacturer, "Manufacturer should be None for empty input")
        
        # Clean up for next iteration
        medicine.delete()
    
    @given(
        whitespace_string=st.text(
            alphabet=string.whitespace,
            min_size=1,
            max_size=10
        ),
        test_id=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=100)
    def test_whitespace_manufacturer_normalization(self, whitespace_string, test_id):
        """
        **Feature: admin-medicine-form-fix, Property 2: Whitespace manufacturer normalization**
        
        For any valid medicine form data where the manufacturer field contains only whitespace characters,
        the form processing should normalize it to None and save successfully
        """
        form_data = self.get_base_form_data(f"ws_mfg_{test_id}")
        form_data['manufacturer'] = whitespace_string  # Whitespace-only manufacturer
        
        response = self.client.post(reverse('admin_medicine_add'), form_data)
        
        # Verify medicine was created successfully
        medicine = Medicine.objects.filter(name=form_data['name']).first()
        self.assertIsNotNone(medicine, "Medicine should be created with whitespace-only manufacturer")
        self.assertIsNone(medicine.manufacturer, "Manufacturer should be None for whitespace-only input")
        
        # Clean up for next iteration
        medicine.delete()
    
    @given(
        manufacturer_name=st.text(
            alphabet=string.ascii_letters + string.digits + ' .-',
            min_size=1,
            max_size=100
        ).filter(lambda x: x.strip()),  # Ensure non-empty after stripping
        test_id=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=100)
    def test_valid_manufacturer_preservation(self, manufacturer_name, test_id):
        """
        **Feature: admin-medicine-form-fix, Property 3: Valid manufacturer preservation**
        
        For any valid medicine form data with a non-empty manufacturer string,
        the form processing should save the medicine with the manufacturer field exactly as provided
        """
        form_data = self.get_base_form_data(f"valid_mfg_{test_id}")
        form_data['manufacturer'] = manufacturer_name
        
        response = self.client.post(reverse('admin_medicine_add'), form_data)
        
        # Verify medicine was created successfully
        medicine = Medicine.objects.filter(name=form_data['name']).first()
        self.assertIsNotNone(medicine, "Medicine should be created with valid manufacturer")
        self.assertEqual(
            medicine.manufacturer, 
            manufacturer_name.strip(),  # Should match the stripped version
            "Manufacturer should be preserved exactly as provided (after stripping)"
        )
        
        # Clean up for next iteration
        medicine.delete()
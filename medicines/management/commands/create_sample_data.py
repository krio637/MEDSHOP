from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from medicines.models import Category, Medicine
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Create sample data for the medicine store'

    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            {'name': 'Pain Relief', 'description': 'Medicines for pain management and relief'},
            {'name': 'Cold & Flu', 'description': 'Treatments for cold and flu symptoms'},
            {'name': 'Digestive Health', 'description': 'Medicines for digestive issues'},
            {'name': 'Vitamins & Supplements', 'description': 'Health supplements and vitamins'},
            {'name': 'First Aid', 'description': 'First aid and wound care products'},
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create medicines
        medicines_data = [
            {
                'name': 'Ibuprofen 200mg',
                'category': 'Pain Relief',
                'description': 'Effective pain relief for headaches, muscle pain, and inflammation.',
                'price': 149.99,
                'stock_quantity': 50,
                'prescription_type': 'OTC',
                'manufacturer': 'HealthCorp',
            },
            {
                'name': 'Paracetamol 500mg',
                'category': 'Pain Relief',
                'description': 'Fast-acting pain reliever and fever reducer.',
                'price': 89.99,
                'stock_quantity': 75,
                'prescription_type': 'OTC',
                'manufacturer': 'MediPharm',
            },
            {
                'name': 'Cough Syrup',
                'category': 'Cold & Flu',
                'description': 'Soothes cough and throat irritation.',
                'price': 225.50,
                'stock_quantity': 30,
                'prescription_type': 'OTC',
                'manufacturer': 'ColdCare',
            },
            {
                'name': 'Vitamin C 1000mg',
                'category': 'Vitamins & Supplements',
                'description': 'Immune system support with high-potency Vitamin C.',
                'price': 299.99,
                'stock_quantity': 100,
                'prescription_type': 'OTC',
                'manufacturer': 'VitaLife',
            },
            {
                'name': 'Antacid Tablets',
                'category': 'Digestive Health',
                'description': 'Fast relief from heartburn and acid indigestion.',
                'price': 179.99,
                'stock_quantity': 60,
                'prescription_type': 'OTC',
                'manufacturer': 'DigestEase',
            },
            {
                'name': 'Antibiotic Cream',
                'category': 'First Aid',
                'description': 'Prevents infection in minor cuts and scrapes.',
                'price': 125.50,
                'stock_quantity': 40,
                'prescription_type': 'OTC',
                'manufacturer': 'FirstAid Plus',
            },
            {
                'name': 'Prescription Pain Relief',
                'category': 'Pain Relief',
                'description': 'Strong pain medication for severe pain management.',
                'price': 499.99,
                'stock_quantity': 20,
                'prescription_type': 'RX',
                'manufacturer': 'PharmaCorp',
            },
        ]

        for med_data in medicines_data:
            category = Category.objects.get(name=med_data['category'])
            medicine, created = Medicine.objects.get_or_create(
                name=med_data['name'],
                defaults={
                    'category': category,
                    'description': med_data['description'],
                    'price': med_data['price'],
                    'stock_quantity': med_data['stock_quantity'],
                    'prescription_type': med_data['prescription_type'],
                    'manufacturer': med_data['manufacturer'],
                    'expiry_date': date.today() + timedelta(days=365),
                }
            )
            if created:
                self.stdout.write(f'Created medicine: {medicine.name}')

        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@medshop.com', 'admin123')
            self.stdout.write('Created superuser: admin (password: admin123)')

        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
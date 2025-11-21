from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from medicines.models import Medicine, Order, OrderItem
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Create test orders for reports and analytics'

    def handle(self, *args, **options):
        # Get existing users and medicines
        users = User.objects.filter(is_staff=False)
        medicines = Medicine.objects.filter(is_active=True)
        
        if not users.exists():
            self.stdout.write(self.style.WARNING('No regular users found. Creating test user...'))
            test_user = User.objects.create_user(
                username='testcustomer',
                email='customer@test.com',
                password='test123',
                first_name='Test',
                last_name='Customer'
            )
            users = [test_user]
        
        if not medicines.exists():
            self.stdout.write(self.style.ERROR('No medicines found. Please add medicines first.'))
            return
        
        # Create test orders for the last 30 days
        orders_created = 0
        for i in range(30):
            order_date = date.today() - timedelta(days=i)
            
            # Create 1-5 orders per day randomly
            daily_orders = random.randint(1, 5)
            
            for _ in range(daily_orders):
                user = random.choice(users)
                
                # Create order
                order = Order.objects.create(
                    user=user,
                    total_amount=0,  # Will be calculated
                    status=random.choice(['PENDING', 'CONFIRMED', 'SHIPPED', 'DELIVERED']),
                    shipping_address=f"123 Test Street, Test City, TC 12345",
                    phone_number="+1-555-0123"
                )
                order.created_at = order_date
                order.save()
                
                # Add 1-3 items to each order
                total_amount = 0
                items_count = random.randint(1, 3)
                
                for _ in range(items_count):
                    medicine = random.choice(medicines)
                    quantity = random.randint(1, 3)
                    
                    OrderItem.objects.create(
                        order=order,
                        medicine=medicine,
                        quantity=quantity,
                        price=medicine.price
                    )
                    
                    total_amount += float(medicine.price) * quantity
                
                # Update order total
                order.total_amount = total_amount
                order.save()
                
                orders_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {orders_created} test orders!')
        )
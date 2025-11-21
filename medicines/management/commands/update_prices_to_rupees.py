from django.core.management.base import BaseCommand
from medicines.models import Medicine

class Command(BaseCommand):
    help = 'Update existing medicine prices from dollars to rupees'

    def handle(self, *args, **options):
        # Conversion rate: 1 USD = 83 INR (approximate)
        conversion_rate = 83
        
        medicines = Medicine.objects.all()
        updated_count = 0
        
        for medicine in medicines:
            # If price is less than 100, assume it's in dollars and convert
            if medicine.price < 100:
                old_price = medicine.price
                medicine.price = round(old_price * conversion_rate, 2)
                medicine.save()
                
                self.stdout.write(
                    f'Updated {medicine.name}: ${old_price} → ₹{medicine.price}'
                )
                updated_count += 1
        
        if updated_count == 0:
            self.stdout.write(
                self.style.SUCCESS('All medicines already have rupee pricing!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} medicine prices to rupees!')
            )
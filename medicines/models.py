from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True, help_text="Category image")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class Medicine(models.Model):
    PRESCRIPTION_CHOICES = [
        ('OTC', 'Over the Counter'),
        ('RX', 'Prescription Required'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    mrp = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="MRP", help_text="Maximum Retail Price")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Selling Price")
    stock_quantity = models.PositiveIntegerField()
    prescription_type = models.CharField(max_length=3, choices=PRESCRIPTION_CHOICES, default='OTC')
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to='medicines/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('medicine_detail', kwargs={'pk': self.pk})
    
    @property
    def discount_percentage(self):
        if self.mrp and self.mrp > self.price:
            return int(((self.mrp - self.price) / self.mrp) * 100)
        return 0
    
    @property
    def savings(self):
        if self.mrp and self.mrp > self.price:
            return self.mrp - self.price
        return 0

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Cart for {self.user.username}"
    
    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.medicine.name}"
    
    def get_total_price(self):
        return self.quantity * self.medicine.price

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    shipping_address = models.TextField()
    phone_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.user:
            return f"Order #{self.id} - {self.user.username}"
        return f"Order #{self.id} - Guest"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity} x {self.medicine.name}"
class MedicineImage(models.Model):
    medicine = models.ForeignKey(Medicine, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='medicines/gallery/')
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alternative text for accessibility")
    is_primary = models.BooleanField(default=False, help_text="Set as primary/featured image")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', '-uploaded_at']
    
    def __str__(self):
        return f"{self.medicine.name} - Image {self.id}"
    
    def save(self, *args, **kwargs):
        # If this is set as primary, remove primary from other images
        if self.is_primary:
            MedicineImage.objects.filter(medicine=self.medicine, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

class SiteSettings(models.Model):
    """Store social media links and other site-wide settings"""
    facebook_url = models.URLField(blank=True, null=True, help_text="Facebook page URL")
    instagram_url = models.URLField(blank=True, null=True, help_text="Instagram profile URL")
    youtube_url = models.URLField(blank=True, null=True, help_text="YouTube channel URL")
    twitter_url = models.URLField(blank=True, null=True, help_text="Twitter profile URL")
    linkedin_url = models.URLField(blank=True, null=True, help_text="LinkedIn profile URL")
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True, help_text="WhatsApp number with country code")
    website_url = models.URLField(blank=True, null=True, help_text="Main website URL for Follow Us section")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return "Site Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        if not self.pk and SiteSettings.objects.exists():
            raise ValueError("Only one SiteSettings instance is allowed")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create the site settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

class ContactMessage(models.Model):
    """Store customer contact form submissions"""
    name = models.CharField(max_length=100, help_text="Customer's full name")
    email = models.EmailField(help_text="Customer's email address")
    subject = models.CharField(max_length=200, help_text="Message subject")
    message = models.TextField(help_text="Message content")
    is_read = models.BooleanField(default=False, help_text="Whether admin has read this message")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of sender")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    def mark_as_read(self):
        """Mark this message as read"""
        self.is_read = True
        self.save(update_fields=['is_read'])
    
    def mark_as_unread(self):
        """Mark this message as unread"""
        self.is_read = False
        self.save(update_fields=['is_read'])


class CustomerFeedback(models.Model):
    """Store customer feedback and ratings"""
    RATING_CHOICES = [
        (1, 'Bad'),
        (2, 'Poor'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    
    name = models.CharField(max_length=100, help_text="Customer's name")
    email = models.EmailField(blank=True, null=True, help_text="Customer's email (optional)")
    rating = models.IntegerField(choices=RATING_CHOICES, help_text="Rating from 1-5")
    feedback = models.TextField(blank=True, help_text="Customer's feedback message")
    is_approved = models.BooleanField(default=False, help_text="Approve to show on website")
    is_featured = models.BooleanField(default=False, help_text="Show in featured testimonials")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Customer Feedback"
        verbose_name_plural = "Customer Feedbacks"
    
    def __str__(self):
        return f"{self.name} - {self.get_rating_display()}"
    
    @property
    def rating_emoji(self):
        """Return emoji based on rating"""
        emojis = {1: '😞', 2: '😕', 3: '😐', 4: '🙂', 5: '😊'}
        return emojis.get(self.rating, '😐')


class ProductFeedback(models.Model):
    """Store product-specific feedback and ratings"""
    RATING_CHOICES = [
        (1, 'Bad'),
        (2, 'Poor'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='feedbacks')
    name = models.CharField(max_length=100, help_text="Customer's name")
    email = models.EmailField(blank=True, null=True, help_text="Customer's email (optional)")
    rating = models.IntegerField(choices=RATING_CHOICES, help_text="Rating from 1-5")
    feedback = models.TextField(blank=True, help_text="Customer's feedback message")
    is_approved = models.BooleanField(default=False, help_text="Approve to show on product page")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Product Feedback"
        verbose_name_plural = "Product Feedbacks"
    
    def __str__(self):
        return f"{self.name} - {self.medicine.name} - {self.get_rating_display()}"
    
    @property
    def rating_emoji(self):
        """Return emoji based on rating"""
        emojis = {1: '😞', 2: '😕', 3: '😐', 4: '🙂', 5: '😊'}
        return emojis.get(self.rating, '😐')


class MediaVideo(models.Model):
    """Store media videos like reels, promotional videos, etc."""
    VIDEO_TYPE_CHOICES = [
        ('REEL', 'Reel'),
        ('PROMO', 'Promotional Video'),
        ('TESTIMONIAL', 'Customer Testimonial'),
        ('TUTORIAL', 'Tutorial/How-to'),
        ('NEWS', 'News/Press'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=200, help_text="Video title")
    description = models.TextField(blank=True, help_text="Video description")
    video_type = models.CharField(max_length=20, choices=VIDEO_TYPE_CHOICES, default='REEL')
    
    # Video can be uploaded or embedded from YouTube/Instagram
    video_file = models.FileField(upload_to='media/videos/', blank=True, null=True, help_text="Upload video file (MP4 recommended)")
    video_url = models.URLField(blank=True, null=True, help_text="YouTube or Instagram video URL (for embedding)")
    thumbnail = models.ImageField(upload_to='media/thumbnails/', blank=True, null=True, help_text="Video thumbnail image")
    
    is_featured = models.BooleanField(default=False, help_text="Show on homepage or featured section")
    is_active = models.BooleanField(default=True, help_text="Is this video visible on the website")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers appear first)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Media Video"
        verbose_name_plural = "Media Videos"
    
    def __str__(self):
        return f"{self.title} ({self.get_video_type_display()})"
    
    @property
    def embed_url(self):
        """Convert YouTube/Instagram URL to embed URL"""
        if not self.video_url:
            return None
        
        url = self.video_url
        
        # YouTube
        if 'youtube.com/watch' in url:
            video_id = url.split('v=')[1].split('&')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        elif 'youtube.com/shorts/' in url:
            video_id = url.split('shorts/')[1].split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        
        # Instagram Reels
        elif 'instagram.com/reel/' in url or 'instagram.com/p/' in url:
            return url + 'embed/'
        
        return url

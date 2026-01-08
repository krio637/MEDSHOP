from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from datetime import date, timedelta
from .models import Category, Medicine, Cart, CartItem, Order, OrderItem, UserProfile, MedicineImage

# Customize admin site headers
admin.site.site_header = "MedShop Administration"
admin.site.site_title = "MedShop Admin"
admin.site.index_title = "Welcome to MedShop Administration Panel"

# Custom admin filters
class StockLevelFilter(admin.SimpleListFilter):
    title = 'Stock Level'
    parameter_name = 'stock_level'

    def lookups(self, request, model_admin):
        return (
            ('out_of_stock', 'Out of Stock'),
            ('low_stock', 'Low Stock (≤10)'),
            ('in_stock', 'In Stock (>10)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'out_of_stock':
            return queryset.filter(stock_quantity=0)
        if self.value() == 'low_stock':
            return queryset.filter(stock_quantity__gt=0, stock_quantity__lte=10)
        if self.value() == 'in_stock':
            return queryset.filter(stock_quantity__gt=10)

class ExpiryStatusFilter(admin.SimpleListFilter):
    title = 'Expiry Status'
    parameter_name = 'expiry_status'

    def lookups(self, request, model_admin):
        return (
            ('expired', 'Expired'),
            ('expiring_soon', 'Expiring Soon (30 days)'),
            ('valid', 'Valid'),
        )

    def queryset(self, request, queryset):
        today = date.today()
        if self.value() == 'expired':
            return queryset.filter(expiry_date__lt=today)
        if self.value() == 'expiring_soon':
            return queryset.filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30))
        if self.value() == 'valid':
            return queryset.filter(expiry_date__gt=today + timedelta(days=30))

# Add inline for MedicineImage in Medicine admin
class MedicineImageInline(admin.TabularInline):
    model = MedicineImage
    extra = 1
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Preview"

class MedicineInline(admin.TabularInline):
    model = Medicine
    extra = 0
    fields = ['name', 'price', 'stock_quantity', 'prescription_type', 'is_active']
    readonly_fields = []
    show_change_link = True

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description_short', 'medicine_count', 'active_medicines', 'created_at']
    search_fields = ['name', 'description']
    list_per_page = 20
    ordering = ['name']
    inlines = [MedicineInline]
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description')
        }),
    )
    
    def description_short(self, obj):
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = 'Description'
    
    def medicine_count(self, obj):
        count = obj.medicine_set.count()
        url = reverse('admin:medicines_medicine_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}" style="color: #007cba; font-weight: bold;">{}</a>', url, count)
    medicine_count.short_description = 'Total Products'
    
    def active_medicines(self, obj):
        count = obj.medicine_set.filter(is_active=True).count()
        url = reverse('admin:medicines_medicine_changelist') + f'?category__id__exact={obj.id}&is_active__exact=1'
        return format_html('<a href="{}" style="color: #28a745; font-weight: bold;">{}</a>', url, count)
    active_medicines.short_description = 'Active Products'

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'name', 'category', 'price_display', 'mrp_display', 'discount_display', 
                   'stock_status', 'prescription_type', 'manufacturer', 'is_active', 'expiry_status']
    list_filter = ['category', 'prescription_type', 'is_active', 'manufacturer', StockLevelFilter, ExpiryStatusFilter, 'created_at']
    search_fields = ['name', 'manufacturer', 'description']
    list_editable = ['is_active']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['discount_percentage', 'savings', 'created_at', 'updated_at', 'image_preview_large']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'manufacturer')
        }),
        ('Pricing', {
            'fields': ('mrp', 'price', 'discount_percentage', 'savings'),
            'classes': ('collapse',)
        }),
        ('Stock & Prescription', {
            'fields': ('stock_quantity', 'prescription_type', 'expiry_date')
        }),
        ('Media & Status', {
            'fields': ('image', 'image_preview_large', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 4px;" />', obj.image.url)
        return format_html('<div style="width: 40px; height: 40px; background: #f0f0f0; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #999;">No Image</div>')
    image_preview.short_description = 'Image'
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" style="border-radius: 8px;" />', obj.image.url)
        return 'No image uploaded'
    image_preview_large.short_description = 'Image Preview'
    
    def stock_status(self, obj):
        if obj.stock_quantity == 0:
            return format_html('<span style="color: #dc3545; font-weight: bold;">OUT OF STOCK</span>')
        elif obj.stock_quantity <= 10:
            return format_html('<span style="color: #ffc107; font-weight: bold;">{} (LOW STOCK)</span>', obj.stock_quantity)
        else:
            return format_html('<span style="color: #28a745; font-weight: bold;">{}</span>', obj.stock_quantity)
    stock_status.short_description = 'Stock'
    
    def price_display(self, obj):
        return format_html('<span style="color: #28a745; font-weight: bold;">₹{}</span>', obj.price)
    price_display.short_description = 'Price'
    
    def mrp_display(self, obj):
        return format_html('<span style="color: #6c757d;">₹{}</span>', obj.mrp)
    mrp_display.short_description = 'MRP'
    
    def discount_display(self, obj):
        discount = obj.discount_percentage
        if discount > 0:
            return format_html('<span style="color: #dc3545; font-weight: bold;">{}% OFF</span>', discount)
        return '-'
    discount_display.short_description = 'Discount'
    
    def expiry_status(self, obj):
        from datetime import date, timedelta
        today = date.today()
        if obj.expiry_date < today:
            return format_html('<span style="color: #dc3545; font-weight: bold;">EXPIRED</span>')
        elif obj.expiry_date <= today + timedelta(days=30):
            return format_html('<span style="color: #ffc107; font-weight: bold;">EXPIRING SOON</span>')
        else:
            return format_html('<span style="color: #28a745;">VALID</span>')
    expiry_status.short_description = 'Expiry Status'
    
    actions = ['mark_as_active', 'mark_as_inactive', 'mark_as_out_of_stock']
    
    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} medicines marked as active.')
    mark_as_active.short_description = "Mark selected medicines as active"
    
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} medicines marked as inactive.')
    mark_as_inactive.short_description = "Mark selected medicines as inactive"
    
    def mark_as_out_of_stock(self, request, queryset):
        updated = queryset.update(stock_quantity=0)
        self.message_user(request, f'{updated} medicines marked as out of stock.')
    mark_as_out_of_stock.short_description = "Mark selected medicines as out of stock"
    
    inlines = [MedicineImageInline]

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    readonly_fields = ['created_at']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'medicine', 'quantity']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['medicine', 'quantity', 'price']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'id']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline]

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'date_of_birth']
    search_fields = ['user__username', 'user__email', 'phone_number']

@admin.register(MedicineImage)
class MedicineImageAdmin(admin.ModelAdmin):
    list_display = ['medicine', 'image_preview', 'alt_text', 'is_primary', 'uploaded_at']
    list_filter = ['is_primary', 'uploaded_at']
    search_fields = ['medicine__name', 'alt_text']
    readonly_fields = ['uploaded_at', 'image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Preview"


from .models import MediaVideo, CustomerFeedback, ProductFeedback

@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating_display', 'feedback_short', 'is_approved', 'is_featured', 'created_at']
    list_filter = ['rating', 'is_approved', 'is_featured', 'created_at']
    search_fields = ['name', 'email', 'feedback']
    list_editable = ['is_approved', 'is_featured']
    list_per_page = 20
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'email')
        }),
        ('Feedback', {
            'fields': ('rating', 'feedback')
        }),
        ('Display Settings', {
            'fields': ('is_approved', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def rating_display(self, obj):
        colors = {1: '#dc3545', 2: '#fd7e14', 3: '#ffc107', 4: '#28a745', 5: '#198754'}
        emojis = {1: '😞', 2: '😕', 3: '😐', 4: '🙂', 5: '😊'}
        color = colors.get(obj.rating, '#6c757d')
        emoji = emojis.get(obj.rating, '😐')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, emoji, obj.get_rating_display()
        )
    rating_display.short_description = 'Rating'
    
    def feedback_short(self, obj):
        if obj.feedback:
            return obj.feedback[:50] + '...' if len(obj.feedback) > 50 else obj.feedback
        return '-'
    feedback_short.short_description = 'Feedback'
    
    actions = ['approve_feedback', 'unapprove_feedback', 'mark_as_featured']
    
    def approve_feedback(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} feedbacks approved.')
    approve_feedback.short_description = "Approve selected feedbacks"
    
    def unapprove_feedback(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} feedbacks unapproved.')
    unapprove_feedback.short_description = "Unapprove selected feedbacks"
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True, is_approved=True)
        self.message_user(request, f'{updated} feedbacks marked as featured.')
    mark_as_featured.short_description = "Mark as featured"


@admin.register(ProductFeedback)
class ProductFeedbackAdmin(admin.ModelAdmin):
    list_display = ['medicine', 'name', 'rating_display', 'feedback_short', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'medicine', 'created_at']
    search_fields = ['name', 'email', 'feedback', 'medicine__name']
    list_editable = ['is_approved']
    list_per_page = 20
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Product', {
            'fields': ('medicine',)
        }),
        ('Customer Information', {
            'fields': ('name', 'email')
        }),
        ('Feedback', {
            'fields': ('rating', 'feedback')
        }),
        ('Display Settings', {
            'fields': ('is_approved',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def rating_display(self, obj):
        colors = {1: '#dc3545', 2: '#fd7e14', 3: '#ffc107', 4: '#28a745', 5: '#198754'}
        emojis = {1: '😞', 2: '😕', 3: '😐', 4: '🙂', 5: '😊'}
        color = colors.get(obj.rating, '#6c757d')
        emoji = emojis.get(obj.rating, '😐')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, emoji, obj.get_rating_display()
        )
    rating_display.short_description = 'Rating'
    
    def feedback_short(self, obj):
        if obj.feedback:
            return obj.feedback[:50] + '...' if len(obj.feedback) > 50 else obj.feedback
        return '-'
    feedback_short.short_description = 'Feedback'
    
    actions = ['approve_feedback', 'unapprove_feedback']
    
    def approve_feedback(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} product feedbacks approved.')
    approve_feedback.short_description = "Approve selected feedbacks"
    
    def unapprove_feedback(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} product feedbacks unapproved.')
    unapprove_feedback.short_description = "Unapprove selected feedbacks"


@admin.register(MediaVideo)
class MediaVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'video_type', 'thumbnail_preview', 'is_featured', 'is_active', 'order', 'created_at']
    list_filter = ['video_type', 'is_featured', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_featured', 'is_active', 'order']
    list_per_page = 20
    ordering = ['order', '-created_at']
    readonly_fields = ['created_at', 'updated_at', 'thumbnail_preview_large', 'video_preview']
    
    fieldsets = (
        ('Video Information', {
            'fields': ('title', 'description', 'video_type')
        }),
        ('Video Source', {
            'fields': ('video_file', 'video_url', 'video_preview'),
            'description': 'Upload a video file OR provide a YouTube/Instagram URL'
        }),
        ('Thumbnail', {
            'fields': ('thumbnail', 'thumbnail_preview_large')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;" />',
                obj.thumbnail.url
            )
        return format_html('<span style="color: #999;">No thumbnail</span>')
    thumbnail_preview.short_description = 'Thumbnail'
    
    def thumbnail_preview_large(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-width: 300px; border-radius: 8px;" />',
                obj.thumbnail.url
            )
        return 'No thumbnail uploaded'
    thumbnail_preview_large.short_description = 'Thumbnail Preview'
    
    def video_preview(self, obj):
        if obj.video_file:
            return format_html(
                '<video width="300" controls style="border-radius: 8px;"><source src="{}" type="video/mp4">Your browser does not support video.</video>',
                obj.video_file.url
            )
        elif obj.embed_url:
            return format_html(
                '<iframe width="300" height="200" src="{}" frameborder="0" allowfullscreen style="border-radius: 8px;"></iframe>',
                obj.embed_url
            )
        return 'No video uploaded or URL provided'
    video_preview.short_description = 'Video Preview'
    
    actions = ['mark_as_featured', 'remove_from_featured', 'mark_as_active', 'mark_as_inactive']
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} videos marked as featured.')
    mark_as_featured.short_description = "Mark selected as featured"
    
    def remove_from_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} videos removed from featured.')
    remove_from_featured.short_description = "Remove from featured"
    
    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} videos marked as active.')
    mark_as_active.short_description = "Mark selected as active"
    
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} videos marked as inactive.')
    mark_as_inactive.short_description = "Mark selected as inactive"

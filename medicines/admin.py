from django.contrib import admin
from .models import Category, Medicine, Cart, CartItem, Order, OrderItem, UserProfile

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock_quantity', 'prescription_type', 'is_active']
    list_filter = ['category', 'prescription_type', 'is_active', 'manufacturer']
    search_fields = ['name', 'manufacturer']
    list_editable = ['price', 'stock_quantity', 'is_active']

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

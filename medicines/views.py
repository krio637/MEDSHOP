from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Medicine, Category, Cart, CartItem, Order, OrderItem
from .forms import SignUpForm, ProfileForm

def home(request):
    """Homepage with featured medicines"""
    featured_medicines = Medicine.objects.filter(is_active=True)[:8]
    categories = Category.objects.all()
    return render(request, 'medicines/home.html', {
        'featured_medicines': featured_medicines,
        'categories': categories
    })

def medicine_list(request):
    """List all medicines with search and filter"""
    medicines = Medicine.objects.filter(is_active=True)
    categories = Category.objects.all()
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(manufacturer__icontains=query)
        )
    
    # Category filter
    category_id = request.GET.get('category')
    if category_id:
        medicines = medicines.filter(category_id=category_id)
    
    return render(request, 'medicines/medicine_list.html', {
        'medicines': medicines,
        'categories': categories,
        'query': query,
        'selected_category': category_id
    })

def medicine_detail(request, pk):
    """Medicine detail page"""
    medicine = get_object_or_404(Medicine, pk=pk, is_active=True)
    return render(request, 'medicines/medicine_detail.html', {
        'medicine': medicine
    })

@login_required
def add_to_cart(request, medicine_id):
    """Add medicine to cart"""
    medicine = get_object_or_404(Medicine, id=medicine_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        medicine=medicine,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{medicine.name} added to cart!')
    return redirect('cart_detail')

@login_required
def cart_detail(request):
    """Cart detail page"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
    except Cart.DoesNotExist:
        cart_items = []
    
    return render(request, 'medicines/cart_detail.html', {
        'cart_items': cart_items
    })

@login_required
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    
    return redirect('cart_detail')

@login_required
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart!')
    return redirect('cart_detail')

@login_required
def checkout(request):
    """Checkout page"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        
        if not cart_items:
            messages.error(request, 'Your cart is empty!')
            return redirect('cart_detail')
            
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty!')
        return redirect('cart_detail')
    
    if request.method == 'POST':
        # Create order
        total_amount = cart.get_total_price()
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')
        
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            shipping_address=shipping_address,
            phone_number=phone_number
        )
        
        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                medicine=cart_item.medicine,
                quantity=cart_item.quantity,
                price=cart_item.medicine.price
            )
        
        # Clear cart
        cart_items.delete()
        
        messages.success(request, f'Order #{order.id} placed successfully!')
        return redirect('order_detail', order_id=order.id)
    
    return render(request, 'medicines/checkout.html', {
        'cart_items': cart_items,
        'total': cart.get_total_price()
    })

@login_required
def order_detail(request, order_id):
    """Order detail page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'medicines/order_detail.html', {
        'order': order
    })

@login_required
def order_history(request):
    """User's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'medicines/order_history.html', {
        'orders': orders
    })

def signup_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created successfully for {username}! Please log in.')
            return redirect('login')
        else:
            # Add error message if form is invalid
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})

def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'registration/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    
    return render(request, 'registration/login.html')

@login_required
def profile_view(request):
    """User profile page"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    
    # Get user statistics
    total_orders = Order.objects.filter(user=request.user).count()
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    return render(request, 'registration/profile.html', {
        'form': form,
        'total_orders': total_orders,
        'recent_orders': recent_orders
    })

def search_view(request):
    """Advanced search page with filters"""
    medicines = Medicine.objects.filter(is_active=True)
    categories = Category.objects.all()
    manufacturers = Medicine.objects.values_list('manufacturer', flat=True).distinct().order_by('manufacturer')
    
    # Get search parameters
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    manufacturer = request.GET.get('manufacturer', '')
    prescription_type = request.GET.get('prescription_type', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort_by', 'name')
    in_stock_only = request.GET.get('in_stock_only', False)
    
    # Apply filters
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(manufacturer__icontains=query)
        )
    
    if category_id:
        medicines = medicines.filter(category_id=category_id)
    
    if manufacturer:
        medicines = medicines.filter(manufacturer__icontains=manufacturer)
    
    if prescription_type:
        medicines = medicines.filter(prescription_type=prescription_type)
    
    if min_price:
        try:
            medicines = medicines.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            medicines = medicines.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    if in_stock_only:
        medicines = medicines.filter(stock_quantity__gt=0)
    
    # Apply sorting
    if sort_by == 'price_low':
        medicines = medicines.order_by('price')
    elif sort_by == 'price_high':
        medicines = medicines.order_by('-price')
    elif sort_by == 'name':
        medicines = medicines.order_by('name')
    elif sort_by == 'newest':
        medicines = medicines.order_by('-created_at')
    else:
        medicines = medicines.order_by('name')
    
    # Pagination
    paginator = Paginator(medicines, 12)  # Show 12 medicines per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'medicines': page_obj,
        'categories': categories,
        'manufacturers': manufacturers,
        'query': query,
        'selected_category': category_id,
        'selected_manufacturer': manufacturer,
        'selected_prescription_type': prescription_type,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'in_stock_only': in_stock_only,
        'total_results': paginator.count,
    }
    
    return render(request, 'medicines/search.html', context)

def search_suggestions(request):
    """AJAX endpoint for search suggestions"""
    query = request.GET.get('q', '')
    suggestions = []
    
    if len(query) >= 2:
        # Get medicine name suggestions
        medicine_names = Medicine.objects.filter(
            name__icontains=query, 
            is_active=True
        ).values_list('name', flat=True)[:5]
        
        # Get manufacturer suggestions
        manufacturers = Medicine.objects.filter(
            manufacturer__icontains=query, 
            is_active=True
        ).values_list('manufacturer', flat=True).distinct()[:3]
        
        suggestions = list(medicine_names) + list(manufacturers)
    
    return JsonResponse({'suggestions': suggestions})

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
    from .models import CustomerFeedback
    featured_medicines = Medicine.objects.filter(is_active=True)[:8]
    categories = Category.objects.all()
    approved_feedbacks = CustomerFeedback.objects.filter(is_approved=True).order_by('-is_featured', '-created_at')[:6]
    return render(request, 'medicines/home.html', {
        'featured_medicines': featured_medicines,
        'categories': categories,
        'approved_feedbacks': approved_feedbacks,
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
    from .models import ProductFeedback
    medicine = get_object_or_404(Medicine, pk=pk, is_active=True)
    product_feedbacks = ProductFeedback.objects.filter(medicine=medicine, is_approved=True)[:6]
    return render(request, 'medicines/medicine_detail.html', {
        'medicine': medicine,
        'product_feedbacks': product_feedbacks,
    })

def add_to_cart(request, medicine_id):
    """Add medicine to cart (works for both logged-in and guest users)"""
    medicine = get_object_or_404(Medicine, id=medicine_id, is_active=True)
    
    if request.user.is_authenticated:
        # Logged-in user: use database cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            medicine=medicine,
            defaults={'quantity': 1}
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    else:
        # Guest user: use session cart
        cart = request.session.get('cart', {})
        medicine_id_str = str(medicine_id)
        if medicine_id_str in cart:
            cart[medicine_id_str]['quantity'] += 1
        else:
            cart[medicine_id_str] = {
                'quantity': 1,
                'name': medicine.name,
                'price': str(medicine.price),
                'image': medicine.image.url if medicine.image else ''
            }
        request.session['cart'] = cart
        request.session.modified = True
    
    messages.success(request, f'{medicine.name} added to cart!')
    return redirect('cart_detail')

def cart_detail(request):
    """Cart detail page (works for both logged-in and guest users)"""
    cart_items = []
    total = 0
    
    if request.user.is_authenticated:
        # Logged-in user: use database cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()
            total = cart.get_total_price()
        except Cart.DoesNotExist:
            pass
    else:
        # Guest user: use session cart
        session_cart = request.session.get('cart', {})
        for medicine_id, item in session_cart.items():
            try:
                medicine = Medicine.objects.get(id=int(medicine_id))
                cart_items.append({
                    'id': medicine_id,
                    'medicine': medicine,
                    'quantity': item['quantity'],
                    'get_total_price': lambda m=medicine, q=item['quantity']: m.price * q
                })
                total += medicine.price * item['quantity']
            except Medicine.DoesNotExist:
                pass
    
    return render(request, 'medicines/cart_detail.html', {
        'cart_items': cart_items,
        'total': total,
        'is_guest': not request.user.is_authenticated
    })

def update_cart_item(request, item_id):
    """Update cart item quantity"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if request.user.is_authenticated:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
        else:
            # Guest user: update session cart
            cart = request.session.get('cart', {})
            item_id_str = str(item_id)
            if item_id_str in cart:
                if quantity > 0:
                    cart[item_id_str]['quantity'] = quantity
                else:
                    del cart[item_id_str]
                request.session['cart'] = cart
                request.session.modified = True
    
    return redirect('cart_detail')

def remove_from_cart(request, item_id):
    """Remove item from cart"""
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
    else:
        # Guest user: remove from session cart
        cart = request.session.get('cart', {})
        item_id_str = str(item_id)
        if item_id_str in cart:
            del cart[item_id_str]
            request.session['cart'] = cart
            request.session.modified = True
    
    messages.success(request, 'Item removed from cart!')
    return redirect('cart_detail')

def checkout(request):
    """Checkout page (works for both logged-in and guest users)"""
    cart_items = []
    total = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = list(cart.items.all())
            total = cart.get_total_price()
        except Cart.DoesNotExist:
            pass
    else:
        # Guest user: use session cart
        session_cart = request.session.get('cart', {})
        for medicine_id, item in session_cart.items():
            try:
                medicine = Medicine.objects.get(id=int(medicine_id))
                cart_items.append({
                    'medicine': medicine,
                    'quantity': item['quantity'],
                    'get_total_price': lambda m=medicine, q=item['quantity']: m.price * q
                })
                total += medicine.price * item['quantity']
            except Medicine.DoesNotExist:
                pass
    
    if not cart_items:
        messages.error(request, 'Your cart is empty!')
        return redirect('cart_detail')
    
    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')
        customer_name = request.POST.get('customer_name', '')
        customer_email = request.POST.get('customer_email', '')
        
        if request.user.is_authenticated:
            # Logged-in user order
            order = Order.objects.create(
                user=request.user,
                total_amount=total,
                shipping_address=shipping_address,
                phone_number=phone_number
            )
            
            # Create order items from database cart
            cart = Cart.objects.get(user=request.user)
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    medicine=cart_item.medicine,
                    quantity=cart_item.quantity,
                    price=cart_item.medicine.price
                )
            # Clear database cart
            cart.items.all().delete()
        else:
            # Guest user order - create without user
            order = Order.objects.create(
                user=None,
                total_amount=total,
                shipping_address=f"{customer_name}\n{customer_email}\n{shipping_address}",
                phone_number=phone_number
            )
            
            # Create order items from session cart
            session_cart = request.session.get('cart', {})
            for medicine_id, item in session_cart.items():
                try:
                    medicine = Medicine.objects.get(id=int(medicine_id))
                    OrderItem.objects.create(
                        order=order,
                        medicine=medicine,
                        quantity=item['quantity'],
                        price=medicine.price
                    )
                except Medicine.DoesNotExist:
                    pass
            
            # Clear session cart
            request.session['cart'] = {}
            request.session.modified = True
        
        messages.success(request, f'Order #{order.id} placed successfully! We will contact you soon.')
        return redirect('order_success', order_id=order.id)
    
    return render(request, 'medicines/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'is_guest': not request.user.is_authenticated
    })

def order_success(request, order_id):
    """Order success page (accessible to everyone)"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'medicines/order_success.html', {
        'order': order
    })

def track_order(request):
    """Track order for guest users - by phone number or order ID"""
    orders = None
    order = None
    error = None
    search_type = None
    
    if request.method == 'POST':
        order_id = request.POST.get('order_id', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        
        if phone_number and not order_id:
            # Search by phone number only - show all orders
            orders = Order.objects.filter(phone_number=phone_number).order_by('-created_at')
            search_type = 'phone'
            if not orders:
                error = "No orders found with this phone number."
        elif order_id and phone_number:
            # Search by both - show specific order
            try:
                order = Order.objects.get(id=int(order_id), phone_number=phone_number)
                search_type = 'specific'
            except (Order.DoesNotExist, ValueError):
                error = "Order not found. Please check your Order ID and Phone Number."
        elif order_id and not phone_number:
            error = "Please enter your phone number to track the order."
        else:
            error = "Please enter your phone number to track orders."
    
    return render(request, 'medicines/track_order.html', {
        'orders': orders,
        'order': order,
        'error': error,
        'search_type': search_type
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
            try:
                user = form.save()
                username = form.cleaned_data.get('username')
                messages.success(request, f'Account created successfully for {username}! Please log in.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'An error occurred while creating your account: {str(e)}')
        else:
            # Form validation errors will be displayed in the template
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})

def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'registration/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                next_url = request.GET.get('next', 'home')
                # Handle both URL names and full paths
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                elif next_url and next_url != 'home':
                    return redirect(next_url)
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Your account has been disabled. Please contact support.')
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


def terms_conditions(request):
    """Terms and Conditions page"""
    return render(request, 'medicines/terms_conditions.html')

def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'medicines/privacy_policy.html')

def about_us(request):
    """About Us page"""
    return render(request, 'medicines/about_us.html')

def contact_us(request):
    """Contact Us page"""
    return render(request, 'medicines/contact_us.html')

def shipping_policy(request):
    """Shipping Policy page"""
    return render(request, 'medicines/shipping_policy.html')

def return_policy(request):
    """Return Policy page"""
    return render(request, 'medicines/return_policy.html')

def disclaimer(request):
    """Disclaimer page"""
    return render(request, 'medicines/disclaimer.html')

def media_page(request):
    """Media page with videos"""
    from .models import MediaVideo
    videos = MediaVideo.objects.filter(is_active=True)
    featured_videos = videos.filter(is_featured=True)
    reels = videos.filter(video_type='REEL')
    promos = videos.filter(video_type='PROMO')
    testimonials = videos.filter(video_type='TESTIMONIAL')
    
    context = {
        'videos': videos,
        'featured_videos': featured_videos,
        'reels': reels,
        'promos': promos,
        'testimonials': testimonials,
    }
    return render(request, 'medicines/media.html', context)

def work_with_us(request):
    """Work with us page"""
    return render(request, 'medicines/work_with_us.html')

def blog(request):
    """Blog page"""
    return render(request, 'medicines/blog.html')

def collaborate(request):
    """Collaborate / Become Affiliate page"""
    return render(request, 'medicines/collaborate.html')

def consult(request):
    """Consult page"""
    return render(request, 'medicines/consult.html')

def rewards(request):
    """Rewards page"""
    return render(request, 'medicines/rewards.html')

def submit_feedback(request):
    """Submit customer feedback"""
    from .models import CustomerFeedback
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        rating = request.POST.get('rating')
        feedback_text = request.POST.get('feedback', '').strip()
        
        if name and rating:
            try:
                CustomerFeedback.objects.create(
                    name=name,
                    email=email if email else None,
                    rating=int(rating),
                    feedback=feedback_text
                )
                messages.success(request, 'Thank you for your feedback! 🙏')
            except Exception as e:
                messages.error(request, 'Something went wrong. Please try again.')
        else:
            messages.error(request, 'Please provide your name and rating.')
        
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    return redirect('home')


def submit_product_feedback(request, medicine_id):
    """Submit product-specific feedback"""
    from .models import ProductFeedback
    
    medicine = get_object_or_404(Medicine, id=medicine_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        rating = request.POST.get('rating')
        feedback_text = request.POST.get('feedback', '').strip()
        
        if name and rating:
            try:
                ProductFeedback.objects.create(
                    medicine=medicine,
                    name=name,
                    email=email if email else None,
                    rating=int(rating),
                    feedback=feedback_text
                )
                messages.success(request, f'Thank you for reviewing {medicine.name}! 🙏')
            except Exception as e:
                messages.error(request, 'Something went wrong. Please try again.')
        else:
            messages.error(request, 'Please provide your name and rating.')
        
        return redirect('medicine_detail', pk=medicine_id)
    
    return redirect('medicine_detail', pk=medicine_id)

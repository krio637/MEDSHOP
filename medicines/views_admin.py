from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Medicine, Category, Order, OrderItem, Cart, CartItem, UserProfile
from .forms import SignUpForm, ProfileForm
from django.contrib.auth.models import User

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with statistics and overview"""
    # Get statistics
    total_medicines = Medicine.objects.count()
    active_medicines = Medicine.objects.filter(is_active=True).count()
    out_of_stock = Medicine.objects.filter(stock_quantity=0).count()
    low_stock = Medicine.objects.filter(stock_quantity__lte=10, stock_quantity__gt=0).count()
    
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='PENDING').count()
    total_users = User.objects.count()
    total_revenue = Order.objects.filter(status='DELIVERED').aggregate(
        total=Sum('total_amount'))['total'] or 0
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    # Low stock medicines
    low_stock_medicines = Medicine.objects.filter(
        stock_quantity__lte=10, is_active=True
    ).order_by('stock_quantity')[:10]
    
    # Monthly revenue data for chart
    monthly_revenue = []
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        revenue = Order.objects.filter(
            created_at__range=[month_start, month_end],
            status='DELIVERED'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        monthly_revenue.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(revenue)
        })
    
    context = {
        'total_medicines': total_medicines,
        'active_medicines': active_medicines,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_users': total_users,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'low_stock_medicines': low_stock_medicines,
        'monthly_revenue': monthly_revenue[::-1],  # Reverse for chronological order
    }
    
    return render(request, 'admin/dashboard.html', context)

@staff_member_required
def admin_medicines(request):
    """Manage medicines"""
    medicines = Medicine.objects.all().select_related('category')
    categories = Category.objects.all()
    
    # Filters
    category_filter = request.GET.get('category')
    stock_filter = request.GET.get('stock')
    search = request.GET.get('search')
    
    if category_filter:
        medicines = medicines.filter(category_id=category_filter)
    
    if stock_filter == 'out_of_stock':
        medicines = medicines.filter(stock_quantity=0)
    elif stock_filter == 'low_stock':
        medicines = medicines.filter(stock_quantity__lte=10, stock_quantity__gt=0)
    elif stock_filter == 'in_stock':
        medicines = medicines.filter(stock_quantity__gt=10)
    
    if search:
        medicines = medicines.filter(
            Q(name__icontains=search) | 
            Q(manufacturer__icontains=search)
        )
    
    medicines = medicines.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(medicines, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'medicines': page_obj,
        'categories': categories,
        'category_filter': category_filter,
        'stock_filter': stock_filter,
        'search': search,
    }
    
    return render(request, 'admin/medicines.html', context)

@staff_member_required
def admin_medicine_edit(request, medicine_id=None):
    """Add or edit medicine"""
    medicine = None
    if medicine_id:
        medicine = get_object_or_404(Medicine, id=medicine_id)
    
    categories = Category.objects.all()
    
    if request.method == 'POST':
        # Handle form submission
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock_quantity = request.POST.get('stock_quantity')
        prescription_type = request.POST.get('prescription_type')
        manufacturer = request.POST.get('manufacturer')
        expiry_date = request.POST.get('expiry_date')
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            if medicine:
                # Update existing medicine
                medicine.name = name
                medicine.category_id = category_id
                medicine.description = description
                medicine.price = float(price)
                medicine.stock_quantity = int(stock_quantity)
                medicine.prescription_type = prescription_type
                medicine.manufacturer = manufacturer
                medicine.expiry_date = expiry_date
                medicine.is_active = is_active
                medicine.save()
                messages.success(request, f'Medicine "{name}" updated successfully!')
            else:
                # Create new medicine
                Medicine.objects.create(
                    name=name,
                    category_id=category_id,
                    description=description,
                    price=float(price),
                    stock_quantity=int(stock_quantity),
                    prescription_type=prescription_type,
                    manufacturer=manufacturer,
                    expiry_date=expiry_date,
                    is_active=is_active
                )
                messages.success(request, f'Medicine "{name}" added successfully!')
            
            return redirect('admin_medicines')
        except Exception as e:
            messages.error(request, f'Error saving medicine: {str(e)}')
    
    context = {
        'medicine': medicine,
        'categories': categories,
    }
    
    return render(request, 'admin/medicine_form.html', context)

@staff_member_required
def admin_medicine_delete(request, medicine_id):
    """Delete medicine"""
    medicine = get_object_or_404(Medicine, id=medicine_id)
    
    if request.method == 'POST':
        medicine_name = medicine.name
        medicine.delete()
        messages.success(request, f'Medicine "{medicine_name}" deleted successfully!')
        return redirect('admin_medicines')
    
    return render(request, 'admin/medicine_delete.html', {'medicine': medicine})

@staff_member_required
def admin_orders(request):
    """Manage orders"""
    orders = Order.objects.all().select_related('user').prefetch_related('items__medicine')
    
    # Filters
    status_filter = request.GET.get('status')
    date_filter = request.GET.get('date')
    search = request.GET.get('search')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if date_filter == 'today':
        orders = orders.filter(created_at__date=timezone.now().date())
    elif date_filter == 'week':
        week_ago = timezone.now() - timedelta(days=7)
        orders = orders.filter(created_at__gte=week_ago)
    elif date_filter == 'month':
        month_ago = timezone.now() - timedelta(days=30)
        orders = orders.filter(created_at__gte=month_ago)
    
    if search:
        orders = orders.filter(
            Q(id__icontains=search) | 
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search)
        )
    
    orders = orders.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search': search,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'admin/orders.html', context)

@staff_member_required
def admin_order_detail(request, order_id):
    """View and manage order details"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Order #{order.id} status updated to {order.get_status_display()}')
            return redirect('admin_order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'admin/order_detail.html', context)

@staff_member_required
def admin_categories(request):
    """Manage categories"""
    categories = Category.objects.annotate(
        medicine_count=Count('medicine')
    ).order_by('name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name = request.POST.get('name')
            description = request.POST.get('description')
            
            if name:
                Category.objects.create(name=name, description=description)
                messages.success(request, f'Category "{name}" added successfully!')
            else:
                messages.error(request, 'Category name is required!')
        
        elif action == 'edit':
            category_id = request.POST.get('category_id')
            name = request.POST.get('name')
            description = request.POST.get('description')
            
            try:
                category = Category.objects.get(id=category_id)
                category.name = name
                category.description = description
                category.save()
                messages.success(request, f'Category "{name}" updated successfully!')
            except Category.DoesNotExist:
                messages.error(request, 'Category not found!')
        
        elif action == 'delete':
            category_id = request.POST.get('category_id')
            try:
                category = Category.objects.get(id=category_id)
                if category.medicine_set.count() > 0:
                    messages.error(request, f'Cannot delete category "{category.name}" - it has medicines!')
                else:
                    category_name = category.name
                    category.delete()
                    messages.success(request, f'Category "{category_name}" deleted successfully!')
            except Category.DoesNotExist:
                messages.error(request, 'Category not found!')
        
        return redirect('admin_categories')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'admin/categories.html', context)

@staff_member_required
def admin_users(request):
    """Manage users"""
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    users = User.objects.all().select_related('profile').annotate(
        order_count=Count('order'),
        total_spent=Sum('order__total_amount')
    )
    
    # Calculate statistics
    total_users = users.count()
    active_customers = users.filter(order_count__gt=0).count()
    staff_members = users.filter(is_staff=True).count()
    
    # New users this month
    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_this_month = users.filter(date_joined__gte=month_start).count()
    
    search = request.GET.get('search')
    user_type = request.GET.get('user_type')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if user_type == 'staff':
        users = users.filter(is_staff=True)
    elif user_type == 'customers':
        users = users.filter(is_staff=False)
    elif user_type == 'active':
        users = users.filter(order_count__gt=0)
    
    users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'search': search,
        'user_type': user_type,
        'total_users': total_users,
        'active_customers': active_customers,
        'staff_members': staff_members,
        'new_this_month': new_this_month,
    }
    
    return render(request, 'admin/users.html', context)

@staff_member_required
def admin_reports(request):
    """Generate reports and analytics"""
    # Sales report
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Revenue statistics
    today_revenue = Order.objects.filter(
        created_at__date=today, status='DELIVERED'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    yesterday_revenue = Order.objects.filter(
        created_at__date=yesterday, status='DELIVERED'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    week_revenue = Order.objects.filter(
        created_at__date__gte=week_ago, status='DELIVERED'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    month_revenue = Order.objects.filter(
        created_at__date__gte=month_ago, status='DELIVERED'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Order statistics
    today_orders = Order.objects.filter(created_at__date=today).count()
    week_orders = Order.objects.filter(created_at__date__gte=week_ago).count()
    month_orders = Order.objects.filter(created_at__date__gte=month_ago).count()
    
    # Top selling medicines
    top_medicines = Medicine.objects.annotate(
        total_sold=Sum('orderitem__quantity'),
        total_revenue=Sum('orderitem__quantity') * Sum('orderitem__price')
    ).filter(total_sold__isnull=False).order_by('-total_sold')[:10]
    
    # Category performance
    category_performance = Category.objects.annotate(
        total_revenue=Sum('medicine__orderitem__price'),
        total_orders=Count('medicine__orderitem__order', distinct=True)
    ).filter(total_revenue__isnull=False).order_by('-total_revenue')[:10]
    
    # Customer insights
    total_customers = User.objects.filter(is_staff=False).count()
    active_customers = User.objects.filter(is_staff=False, order__isnull=False).distinct().count()
    new_customers = User.objects.filter(
        is_staff=False, 
        date_joined__gte=month_ago
    ).count()
    
    # Calculate retention rate (customers who made more than one order)
    repeat_customers = User.objects.filter(is_staff=False).annotate(
        order_count=Count('order')
    ).filter(order_count__gt=1).count()
    
    retention_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
    
    context = {
        'today_revenue': today_revenue,
        'yesterday_revenue': yesterday_revenue,
        'week_revenue': week_revenue,
        'month_revenue': month_revenue,
        'today_orders': today_orders,
        'week_orders': week_orders,
        'month_orders': month_orders,
        'top_medicines': top_medicines,
        'category_performance': category_performance,
        'total_customers': total_customers,
        'active_customers': active_customers,
        'new_customers': new_customers,
        'retention_rate': retention_rate,
    }
    
    return render(request, 'admin/reports.html', context)

@staff_member_required
def admin_bulk_actions(request):
    """Handle bulk actions"""
    if request.method == 'POST':
        action = request.POST.get('action')
        medicine_ids = request.POST.getlist('medicine_ids')
        
        if not medicine_ids:
            messages.error(request, 'No medicines selected!')
            return redirect('admin_medicines')
        
        medicines = Medicine.objects.filter(id__in=medicine_ids)
        
        if action == 'activate':
            medicines.update(is_active=True)
            messages.success(request, f'{len(medicine_ids)} medicines activated!')
        
        elif action == 'deactivate':
            medicines.update(is_active=False)
            messages.success(request, f'{len(medicine_ids)} medicines deactivated!')
        
        elif action == 'delete_out_of_stock':
            out_of_stock = medicines.filter(stock_quantity=0)
            count = out_of_stock.count()
            out_of_stock.delete()
            messages.success(request, f'{count} out-of-stock medicines deleted!')
        
        elif action == 'update_stock':
            new_stock = request.POST.get('new_stock')
            if new_stock:
                medicines.update(stock_quantity=int(new_stock))
                messages.success(request, f'Stock updated for {len(medicine_ids)} medicines!')
    
    return redirect('admin_medicines')

@staff_member_required
def generate_report(request):
    """Generate and download reports"""
    from django.http import HttpResponse
    import csv
    
    report_type = request.GET.get('type', 'daily')
    
    if report_type == 'daily':
        # Generate daily sales report
        today = timezone.now().date()
        orders = Order.objects.filter(created_at__date=today)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="daily_sales_{today}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Customer', 'Total Amount', 'Status', 'Time'])
        
        for order in orders:
            writer.writerow([
                order.id,
                f"{order.user.first_name} {order.user.last_name}",
                order.total_amount,
                order.get_status_display(),
                order.created_at.strftime('%H:%M:%S')
            ])
        
        return response
    
    elif report_type == 'inventory':
        # Generate inventory report
        medicines = Medicine.objects.all()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Medicine Name', 'Category', 'Price', 'Stock', 'Status', 'Manufacturer'])
        
        for medicine in medicines:
            writer.writerow([
                medicine.name,
                medicine.category.name,
                medicine.price,
                medicine.stock_quantity,
                'Active' if medicine.is_active else 'Inactive',
                medicine.manufacturer
            ])
        
        return response
    
    # Default: redirect back to reports
    messages.info(request, f'{report_type.title()} report generated successfully!')
    return redirect('admin_reports')
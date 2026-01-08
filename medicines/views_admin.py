from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Medicine, Category, Order, OrderItem, Cart, CartItem, UserProfile, MedicineImage
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
    
    # Top categories with product counts
    top_categories = Category.objects.annotate(
        medicine_count=Count('medicine'),
        active_count=Count('medicine', filter=Q(medicine__is_active=True))
    ).order_by('-medicine_count')[:5]
    
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
        'top_categories': top_categories,
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
        mrp = request.POST.get('mrp')
        price = request.POST.get('price')
        stock_quantity = request.POST.get('stock_quantity')
        prescription_type = request.POST.get('prescription_type')
        
        # Handle optional fields - convert empty/whitespace strings to None
        manufacturer = request.POST.get('manufacturer', '').strip() or None
        expiry_date = request.POST.get('expiry_date', '').strip() or None
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            if medicine:
                # Update existing medicine
                medicine.name = name
                medicine.category_id = category_id
                medicine.description = description
                medicine.mrp = float(mrp) if mrp else float(price)
                medicine.price = float(price)
                medicine.stock_quantity = int(stock_quantity)
                medicine.prescription_type = prescription_type
                medicine.manufacturer = manufacturer
                medicine.expiry_date = expiry_date
                medicine.is_active = is_active
                
                # Handle main image upload
                if 'image' in request.FILES:
                    medicine.image = request.FILES['image']
                
                medicine.save()
                
                # Handle multiple image uploads
                if 'gallery_images' in request.FILES:
                    gallery_images = request.FILES.getlist('gallery_images')
                    for i, image_file in enumerate(gallery_images):
                        alt_text = request.POST.get(f'new_alt_text_{i}', '')
                        MedicineImage.objects.create(
                            medicine=medicine,
                            image=image_file,
                            alt_text=alt_text
                        )
                
                # Handle existing image updates
                for img in medicine.images.all():
                    # Update alt text
                    alt_text_key = f'alt_text_{img.id}'
                    if alt_text_key in request.POST:
                        img.alt_text = request.POST[alt_text_key]
                        img.save()
                
                # Handle primary image setting
                primary_image_id = request.POST.get('primary_image')
                if primary_image_id:
                    # Reset all to non-primary
                    medicine.images.update(is_primary=False)
                    # Set selected as primary
                    medicine.images.filter(id=primary_image_id).update(is_primary=True)
                
                # Handle image deletions
                delete_images = request.POST.getlist('delete_images')
                if delete_images:
                    MedicineImage.objects.filter(id__in=delete_images).delete()
                
                messages.success(request, f'Medicine "{name}" updated successfully!')
            else:
                # Create new medicine
                medicine = Medicine.objects.create(
                    name=name,
                    category_id=category_id,
                    description=description,
                    mrp=float(mrp) if mrp else float(price),
                    price=float(price),
                    stock_quantity=int(stock_quantity),
                    prescription_type=prescription_type,
                    manufacturer=manufacturer,
                    expiry_date=expiry_date,
                    is_active=is_active
                )
                
                # Handle main image upload
                if 'image' in request.FILES:
                    medicine.image = request.FILES['image']
                    medicine.save()
                
                # Handle multiple image uploads
                if 'gallery_images' in request.FILES:
                    gallery_images = request.FILES.getlist('gallery_images')
                    for i, image_file in enumerate(gallery_images):
                        alt_text = request.POST.get(f'new_alt_text_{i}', '')
                        is_primary = i == 0 and not medicine.image  # First image is primary if no main image
                        MedicineImage.objects.create(
                            medicine=medicine,
                            image=image_file,
                            alt_text=alt_text,
                            is_primary=is_primary
                        )
                
                messages.success(request, f'Medicine "{name}" added successfully!')
            
            return redirect('admin_medicines')
        except Exception as e:
            import traceback
            print(f"Error in medicine form: {str(e)}")
            print(traceback.format_exc())
            
            # Provide more specific error messages
            if 'NOT NULL constraint failed' in str(e):
                if 'manufacturer' in str(e):
                    messages.error(request, 'Error: Manufacturer field processing failed. Please try again or leave it blank.')
                else:
                    messages.error(request, f'Database constraint error: {str(e)}')
            else:
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
    )
    
    # Search functionality
    search = request.GET.get('search')
    status_filter = request.GET.get('status')
    sort_by = request.GET.get('sort', 'name')
    
    if search:
        categories = categories.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if status_filter == 'active':
        categories = categories.filter(medicine_count__gt=0)
    elif status_filter == 'empty':
        categories = categories.filter(medicine_count=0)
    
    # Sorting
    if sort_by in ['name', '-name', 'created_at', '-created_at']:
        categories = categories.order_by(sort_by)
    else:
        categories = categories.order_by('name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name = request.POST.get('name')
            description = request.POST.get('description')
            image = request.FILES.get('image')
            
            if name:
                category = Category.objects.create(name=name, description=description)
                if image:
                    category.image = image
                    category.save()
                messages.success(request, f'Category "{name}" added successfully!')
            else:
                messages.error(request, 'Category name is required!')
        
        elif action == 'edit':
            category_id = request.POST.get('category_id')
            name = request.POST.get('name')
            description = request.POST.get('description')
            image = request.FILES.get('image')
            
            try:
                category = Category.objects.get(id=category_id)
                category.name = name
                category.description = description
                if image:
                    category.image = image
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
        
        elif action == 'delete_empty':
            empty_categories = Category.objects.annotate(
                medicine_count=Count('medicine')
            ).filter(medicine_count=0)
            count = empty_categories.count()
            empty_categories.delete()
            messages.success(request, f'{count} empty categories deleted successfully!')
        
        elif action == 'bulk_delete':
            category_ids = request.POST.getlist('category_ids')
            if category_ids:
                categories_to_delete = Category.objects.filter(
                    id__in=category_ids
                ).annotate(medicine_count=Count('medicine')).filter(medicine_count=0)
                count = categories_to_delete.count()
                categories_to_delete.delete()
                messages.success(request, f'{count} categories deleted successfully!')
            else:
                messages.error(request, 'No categories selected for deletion!')
        
        elif action == 'bulk_add':
            bulk_categories = request.POST.get('bulk_categories', '').strip()
            auto_descriptions = request.POST.get('auto_descriptions') == 'on'
            
            if bulk_categories:
                category_names = [name.strip() for name in bulk_categories.split('\n') if name.strip()]
                created_count = 0
                
                for name in category_names:
                    if not Category.objects.filter(name__iexact=name).exists():
                        description = ''
                        if auto_descriptions:
                            description = f'Products related to {name.lower()}'
                        
                        Category.objects.create(name=name, description=description)
                        created_count += 1
                
                messages.success(request, f'{created_count} categories added successfully!')
                if len(category_names) > created_count:
                    messages.info(request, f'{len(category_names) - created_count} categories already existed and were skipped.')
            else:
                messages.error(request, 'No category names provided!')
        
        elif action == 'add_templates':
            import json
            template_categories = request.POST.get('template_categories', '[]')
            
            try:
                category_names = json.loads(template_categories)
                created_count = 0
                
                for name in category_names:
                    if not Category.objects.filter(name__iexact=name).exists():
                        description = f'Products related to {name.lower()}'
                        Category.objects.create(name=name, description=description)
                        created_count += 1
                
                messages.success(request, f'{created_count} categories added from templates!')
                if len(category_names) > created_count:
                    messages.info(request, f'{len(category_names) - created_count} categories already existed and were skipped.')
            except json.JSONDecodeError:
                messages.error(request, 'Invalid template data!')
        
        elif action == 'sort_categories':
            # This would require adding an order field to the Category model
            # For now, we'll just show a message
            messages.info(request, 'Categories are displayed in alphabetical order by default.')
        
        return redirect('admin_categories')
    
    context = {
        'categories': categories,
        'search': search,
        'status_filter': status_filter,
        'sort_by': sort_by,
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
        
        elif action == 'delete_selected':
            count = medicines.count()
            medicines.delete()
            messages.success(request, f'{count} selected medicines deleted!')
        
        elif action == 'delete_inactive':
            inactive_medicines = Medicine.objects.filter(is_active=False)
            count = inactive_medicines.count()
            inactive_medicines.delete()
            messages.success(request, f'{count} inactive medicines deleted!')
        
        elif action == 'delete_expired':
            from datetime import date
            expired_medicines = Medicine.objects.filter(expiry_date__lt=date.today())
            count = expired_medicines.count()
            expired_medicines.delete()
            messages.success(request, f'{count} expired medicines deleted!')
        
        elif action == 'mark_low_stock':
            medicines.update(stock_quantity=5)
            messages.success(request, f'{len(medicine_ids)} medicines marked as low stock!')
    
        return redirect('admin_medicines')
    
    # Handle order bulk actions
    elif request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'bulk_status_update':
            order_ids = request.POST.getlist('order_ids')
            new_status = request.POST.get('status')
            
            if not order_ids:
                messages.error(request, 'No orders selected!')
                return redirect('admin_orders')
            
            if new_status not in dict(Order.STATUS_CHOICES):
                messages.error(request, 'Invalid status!')
                return redirect('admin_orders')
            
            orders = Order.objects.filter(id__in=order_ids)
            count = orders.update(status=new_status)
            status_display = dict(Order.STATUS_CHOICES)[new_status]
            messages.success(request, f'{count} orders updated to {status_display}!')
            return redirect('admin_orders')
        
        elif action == 'bulk_delete_orders':
            delete_criteria = request.POST.getlist('delete_criteria')
            order_ids = request.POST.getlist('order_ids')
            
            if not delete_criteria:
                messages.error(request, 'No deletion criteria selected!')
                return redirect('admin_orders')
            
            orders_to_delete = Order.objects.none()
            
            for criterion in delete_criteria:
                if criterion == 'pending':
                    orders_to_delete = orders_to_delete | Order.objects.filter(status='PENDING')
                elif criterion == 'cancelled':
                    orders_to_delete = orders_to_delete | Order.objects.filter(status='CANCELLED')
                elif criterion == 'old_delivered':
                    from datetime import date, timedelta
                    thirty_days_ago = date.today() - timedelta(days=30)
                    orders_to_delete = orders_to_delete | Order.objects.filter(
                        status='DELIVERED', 
                        created_at__date__lt=thirty_days_ago
                    )
                elif criterion == 'selected' and order_ids:
                    orders_to_delete = orders_to_delete | Order.objects.filter(id__in=order_ids)
            
            # Remove duplicates
            orders_to_delete = orders_to_delete.distinct()
            count = orders_to_delete.count()
            
            if count > 0:
                orders_to_delete.delete()
                messages.success(request, f'{count} orders deleted successfully!')
            else:
                messages.info(request, 'No orders matched the deletion criteria.')
            
            return redirect('admin_orders')
    
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

@staff_member_required
def admin_order_add(request):
    """Add new order"""
    if request.method == 'POST':
        # Get form data
        user_id = request.POST.get('user')
        status = request.POST.get('status')
        phone_number = request.POST.get('phone_number')
        total_amount = request.POST.get('total_amount')
        shipping_address = request.POST.get('shipping_address')
        
        # Validate required fields
        if not all([user_id, status, phone_number, total_amount, shipping_address]):
            messages.error(request, 'All fields are required.')
            return redirect('admin_order_add')
        
        try:
            user = User.objects.get(id=user_id)
            
            # Create order
            order = Order.objects.create(
                user=user,
                status=status,
                phone_number=phone_number,
                total_amount=total_amount,
                shipping_address=shipping_address
            )
            
            # Add order items
            item_count = 0
            for key in request.POST.keys():
                if key.startswith('medicine_'):
                    index = key.split('_')[1]
                    medicine_id = request.POST.get(f'medicine_{index}')
                    quantity = request.POST.get(f'quantity_{index}')
                    price = request.POST.get(f'price_{index}')
                    
                    if medicine_id and quantity and price:
                        medicine = Medicine.objects.get(id=medicine_id)
                        OrderItem.objects.create(
                            order=order,
                            medicine=medicine,
                            quantity=int(quantity),
                            price=float(price)
                        )
                        item_count += 1
            
            if item_count == 0:
                order.delete()
                messages.error(request, 'At least one item is required.')
                return redirect('admin_order_add')
            
            messages.success(request, f'Order #{order.id} created successfully!')
            return redirect('admin_order_detail', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
            return redirect('admin_order_add')
    
    # GET request - show form
    customers = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    medicines = Medicine.objects.filter(is_active=True).order_by('name')
    
    context = {
        'customers': customers,
        'medicines': medicines,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'admin/order_form.html', context)

@staff_member_required
def admin_order_edit(request, order_id):
    """Edit existing order"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        # Get form data
        user_id = request.POST.get('user')
        status = request.POST.get('status')
        phone_number = request.POST.get('phone_number')
        total_amount = request.POST.get('total_amount')
        shipping_address = request.POST.get('shipping_address')
        
        # Validate required fields
        if not all([user_id, status, phone_number, total_amount, shipping_address]):
            messages.error(request, 'All fields are required.')
            return redirect('admin_order_edit', order_id=order.id)
        
        try:
            user = User.objects.get(id=user_id)
            
            # Update order
            order.user = user
            order.status = status
            order.phone_number = phone_number
            order.total_amount = total_amount
            order.shipping_address = shipping_address
            order.save()
            
            # Delete existing items and create new ones
            order.items.all().delete()
            
            # Add order items
            item_count = 0
            for key in request.POST.keys():
                if key.startswith('medicine_'):
                    index = key.split('_')[1]
                    medicine_id = request.POST.get(f'medicine_{index}')
                    quantity = request.POST.get(f'quantity_{index}')
                    price = request.POST.get(f'price_{index}')
                    
                    if medicine_id and quantity and price:
                        medicine = Medicine.objects.get(id=medicine_id)
                        OrderItem.objects.create(
                            order=order,
                            medicine=medicine,
                            quantity=int(quantity),
                            price=float(price)
                        )
                        item_count += 1
            
            if item_count == 0:
                messages.error(request, 'At least one item is required.')
                return redirect('admin_order_edit', order_id=order.id)
            
            messages.success(request, f'Order #{order.id} updated successfully!')
            return redirect('admin_order_detail', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f'Error updating order: {str(e)}')
            return redirect('admin_order_edit', order_id=order.id)
    
    # GET request - show form with existing data
    customers = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    medicines = Medicine.objects.filter(is_active=True).order_by('name')
    
    context = {
        'order': order,
        'customers': customers,
        'medicines': medicines,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'admin/order_form.html', context)

@staff_member_required
def admin_order_delete(request, order_id):
    """Delete order"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        order_number = order.id
        order.delete()
        messages.success(request, f'Order #{order_number} deleted successfully!')
        return redirect('admin_orders')
    
    # GET request - show confirmation
    context = {
        'order': order,
    }
    
    return render(request, 'admin/order_delete.html', context)


@staff_member_required
def admin_media(request):
    """Manage media videos"""
    from .models import MediaVideo
    
    videos = MediaVideo.objects.all().order_by('order', '-created_at')
    
    # Filters
    video_type = request.GET.get('type')
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if video_type:
        videos = videos.filter(video_type=video_type)
    
    if status == 'active':
        videos = videos.filter(is_active=True)
    elif status == 'inactive':
        videos = videos.filter(is_active=False)
    elif status == 'featured':
        videos = videos.filter(is_featured=True)
    
    if search:
        videos = videos.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(videos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'videos': page_obj,
        'video_type': video_type,
        'status': status,
        'search': search,
        'video_type_choices': MediaVideo.VIDEO_TYPE_CHOICES,
        'total_videos': MediaVideo.objects.count(),
        'active_videos': MediaVideo.objects.filter(is_active=True).count(),
        'featured_videos': MediaVideo.objects.filter(is_featured=True).count(),
    }
    
    return render(request, 'admin/media.html', context)

@staff_member_required
def admin_media_edit(request, video_id=None):
    """Add or edit media video"""
    from .models import MediaVideo
    
    video = None
    if video_id:
        video = get_object_or_404(MediaVideo, id=video_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        video_type = request.POST.get('video_type', 'REEL')
        video_url = request.POST.get('video_url', '').strip() or None
        is_featured = request.POST.get('is_featured') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        order = request.POST.get('order', 0)
        
        try:
            if video:
                # Update existing
                video.title = title
                video.description = description
                video.video_type = video_type
                video.video_url = video_url
                video.is_featured = is_featured
                video.is_active = is_active
                video.order = int(order) if order else 0
                
                if 'video_file' in request.FILES:
                    video.video_file = request.FILES['video_file']
                if 'thumbnail' in request.FILES:
                    video.thumbnail = request.FILES['thumbnail']
                
                video.save()
                messages.success(request, f'Video "{title}" updated successfully!')
            else:
                # Create new
                video = MediaVideo.objects.create(
                    title=title,
                    description=description,
                    video_type=video_type,
                    video_url=video_url,
                    is_featured=is_featured,
                    is_active=is_active,
                    order=int(order) if order else 0
                )
                
                if 'video_file' in request.FILES:
                    video.video_file = request.FILES['video_file']
                if 'thumbnail' in request.FILES:
                    video.thumbnail = request.FILES['thumbnail']
                video.save()
                
                messages.success(request, f'Video "{title}" added successfully!')
            
            return redirect('admin_media')
        except Exception as e:
            messages.error(request, f'Error saving video: {str(e)}')
    
    context = {
        'video': video,
        'video_type_choices': MediaVideo.VIDEO_TYPE_CHOICES,
    }
    
    return render(request, 'admin/media_form.html', context)

@staff_member_required
def admin_media_delete(request, video_id):
    """Delete media video"""
    from .models import MediaVideo
    
    video = get_object_or_404(MediaVideo, id=video_id)
    
    if request.method == 'POST':
        video_title = video.title
        video.delete()
        messages.success(request, f'Video "{video_title}" deleted successfully!')
        return redirect('admin_media')
    
    return render(request, 'admin/media_delete.html', {'video': video})


@staff_member_required
def admin_social_settings(request):
    """Manage social media links and site settings"""
    from .models import SiteSettings
    
    settings = SiteSettings.get_settings()
    
    if request.method == 'POST':
        try:
            settings.facebook_url = request.POST.get('facebook_url', '').strip() or None
            settings.instagram_url = request.POST.get('instagram_url', '').strip() or None
            settings.youtube_url = request.POST.get('youtube_url', '').strip() or None
            settings.twitter_url = request.POST.get('twitter_url', '').strip() or None
            settings.linkedin_url = request.POST.get('linkedin_url', '').strip() or None
            settings.whatsapp_number = request.POST.get('whatsapp_number', '').strip() or None
            settings.website_url = request.POST.get('website_url', '').strip() or None
            settings.save()
            
            messages.success(request, 'Social media settings updated successfully!')
            return redirect('admin_social_settings')
        except Exception as e:
            messages.error(request, f'Error saving settings: {str(e)}')
    
    context = {
        'settings': settings,
    }
    
    return render(request, 'admin/social_settings.html', context)


@staff_member_required
def admin_feedbacks(request):
    """Manage customer and product feedbacks"""
    from .models import CustomerFeedback, ProductFeedback
    
    feedback_type = request.GET.get('type', 'customer')
    
    if feedback_type == 'product':
        feedbacks = ProductFeedback.objects.all().select_related('medicine').order_by('-created_at')
    else:
        feedbacks = CustomerFeedback.objects.all().order_by('-created_at')
    
    # Filters
    rating_filter = request.GET.get('rating')
    status_filter = request.GET.get('status')
    search = request.GET.get('search')
    
    if rating_filter:
        feedbacks = feedbacks.filter(rating=rating_filter)
    
    if status_filter == 'approved':
        feedbacks = feedbacks.filter(is_approved=True)
    elif status_filter == 'pending':
        feedbacks = feedbacks.filter(is_approved=False)
    elif status_filter == 'featured' and feedback_type == 'customer':
        feedbacks = feedbacks.filter(is_featured=True)
    
    if search:
        if feedback_type == 'product':
            feedbacks = feedbacks.filter(
                Q(name__icontains=search) | 
                Q(email__icontains=search) |
                Q(feedback__icontains=search) |
                Q(medicine__name__icontains=search)
            )
        else:
            feedbacks = feedbacks.filter(
                Q(name__icontains=search) | 
                Q(email__icontains=search) |
                Q(feedback__icontains=search)
            )
    
    # Statistics
    total_customer = CustomerFeedback.objects.count()
    approved_customer = CustomerFeedback.objects.filter(is_approved=True).count()
    total_product = ProductFeedback.objects.count()
    approved_product = ProductFeedback.objects.filter(is_approved=True).count()
    
    # Pagination
    paginator = Paginator(feedbacks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'feedbacks': page_obj,
        'feedback_type': feedback_type,
        'rating_filter': rating_filter,
        'status_filter': status_filter,
        'search': search,
        'total_customer': total_customer,
        'approved_customer': approved_customer,
        'total_product': total_product,
        'approved_product': approved_product,
    }
    
    return render(request, 'admin/feedbacks.html', context)


@staff_member_required
def admin_feedback_action(request, feedback_id):
    """Handle feedback actions (approve, unapprove, feature, delete)"""
    from .models import CustomerFeedback, ProductFeedback
    
    feedback_type = request.GET.get('type', 'customer')
    action = request.POST.get('action')
    
    if feedback_type == 'product':
        feedback = get_object_or_404(ProductFeedback, id=feedback_id)
    else:
        feedback = get_object_or_404(CustomerFeedback, id=feedback_id)
    
    if action == 'approve':
        feedback.is_approved = True
        feedback.save()
        messages.success(request, f'Feedback from "{feedback.name}" approved!')
    elif action == 'unapprove':
        feedback.is_approved = False
        if hasattr(feedback, 'is_featured'):
            feedback.is_featured = False
        feedback.save()
        messages.success(request, f'Feedback from "{feedback.name}" unapproved!')
    elif action == 'feature' and hasattr(feedback, 'is_featured'):
        feedback.is_featured = True
        feedback.is_approved = True
        feedback.save()
        messages.success(request, f'Feedback from "{feedback.name}" marked as featured!')
    elif action == 'unfeature' and hasattr(feedback, 'is_featured'):
        feedback.is_featured = False
        feedback.save()
        messages.success(request, f'Feedback from "{feedback.name}" removed from featured!')
    elif action == 'delete':
        name = feedback.name
        feedback.delete()
        messages.success(request, f'Feedback from "{name}" deleted!')
    
    return redirect(f'/admin-feedbacks/?type={feedback_type}')

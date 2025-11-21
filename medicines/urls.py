from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import views_admin

urlpatterns = [
    path('', views.home, name='home'),
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('search/', views.search_view, name='search'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('medicine/<int:pk>/', views.medicine_detail, name='medicine_detail'),
    path('add-to-cart/<int:medicine_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('update-cart/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/', views.order_history, name='order_history'),
    
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='profile'),
    
    # Admin URLs
    path('admin-dashboard/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('admin-medicines/', views_admin.admin_medicines, name='admin_medicines'),
    path('admin-medicine-add/', views_admin.admin_medicine_edit, name='admin_medicine_add'),
    path('admin-medicine-edit/<int:medicine_id>/', views_admin.admin_medicine_edit, name='admin_medicine_edit'),
    path('admin-medicine-delete/<int:medicine_id>/', views_admin.admin_medicine_delete, name='admin_medicine_delete'),
    path('admin-orders/', views_admin.admin_orders, name='admin_orders'),
    path('admin-order/<int:order_id>/', views_admin.admin_order_detail, name='admin_order_detail'),
    path('admin-categories/', views_admin.admin_categories, name='admin_categories'),
    path('admin-users/', views_admin.admin_users, name='admin_users'),
    path('admin-reports/', views_admin.admin_reports, name='admin_reports'),
    path('admin-bulk-actions/', views_admin.admin_bulk_actions, name='admin_bulk_actions'),
    path('admin-generate-report/', views_admin.generate_report, name='admin_generate_report'),
]
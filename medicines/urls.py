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
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('track-order/', views.track_order, name='track_order'),
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
    path('admin-order-add/', views_admin.admin_order_add, name='admin_order_add'),
    path('admin-order/<int:order_id>/', views_admin.admin_order_detail, name='admin_order_detail'),
    path('admin-order-edit/<int:order_id>/', views_admin.admin_order_edit, name='admin_order_edit'),
    path('admin-order-delete/<int:order_id>/', views_admin.admin_order_delete, name='admin_order_delete'),
    path('admin-categories/', views_admin.admin_categories, name='admin_categories'),
    path('admin-users/', views_admin.admin_users, name='admin_users'),
    path('admin-reports/', views_admin.admin_reports, name='admin_reports'),
    path('admin-bulk-actions/', views_admin.admin_bulk_actions, name='admin_bulk_actions'),
    path('admin-generate-report/', views_admin.generate_report, name='admin_generate_report'),
    path('admin-media/', views_admin.admin_media, name='admin_media'),
    path('admin-media-add/', views_admin.admin_media_edit, name='admin_media_add'),
    path('admin-media-edit/<int:video_id>/', views_admin.admin_media_edit, name='admin_media_edit'),
    path('admin-media-delete/<int:video_id>/', views_admin.admin_media_delete, name='admin_media_delete'),
    path('admin-social-settings/', views_admin.admin_social_settings, name='admin_social_settings'),
    path('admin-feedbacks/', views_admin.admin_feedbacks, name='admin_feedbacks'),
    path('admin-feedback-action/<int:feedback_id>/', views_admin.admin_feedback_action, name='admin_feedback_action'),
    
    # Static pages
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('about-us/', views.about_us, name='about_us'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),
    path('return-policy/', views.return_policy, name='return_policy'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    path('media/', views.media_page, name='media'),
    path('work-with-us/', views.work_with_us, name='work_with_us'),
    path('blog/', views.blog, name='blog'),
    path('collaborate/', views.collaborate, name='collaborate'),
    path('consult/', views.consult, name='consult'),
    path('rewards/', views.rewards, name='rewards'),
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('submit-product-feedback/<int:medicine_id>/', views.submit_product_feedback, name='submit_product_feedback'),
]
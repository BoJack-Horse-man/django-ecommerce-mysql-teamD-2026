"""
URL Configuration for E-Commerce Application

This module defines all URL patterns for the application.
URL patterns are matched in order, so more specific patterns should come first.

Important: Generic slug patterns (like <slug:slug>) MUST be last,
otherwise they will match URLs intended for other views.

Why use named URLs? Makes templates and redirects more maintainable.
Example: {% url 'product_list' %} instead of hardcoding '/products/'
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from shop import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin panel - Django's built-in admin interface
    path('admin/', admin.site.urls),

    # Authentication routes
    # Using Django's built-in LoginView for security best practices
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.user_profile, name='user_profile'),

    # Cart & Checkout routes
    path('cart/', views.cart_summary, name='cart_summary'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('order/<int:order_id>/pay/', views.fake_pay, name='fake_pay'),

    # Wishlist routes
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # Review routes
    path('review/add/<int:product_id>/', views.add_review, name='add_review'),

    # Information pages
    path('about/', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),
    path('faq/', views.faq, name='faq'),

    # Newsletter routes
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('newsletter/unsubscribe/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),

    # Home & Products (must come before generic slug pattern)
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    
    # Product detail route (generic slug pattern - MUST be last!)
    # This matches any slug, so it must come after all other specific patterns
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]

# Serve media files during development
# Why only in DEBUG mode? In production, web server (nginx/apache) should serve static/media files
# This is a security and performance best practice
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
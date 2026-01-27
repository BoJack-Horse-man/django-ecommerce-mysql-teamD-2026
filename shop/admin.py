"""
Django Admin Configuration for E-Commerce Application

This module configures the Django admin interface for managing the e-commerce store.
Admin classes customize how models appear and behave in the admin panel.

Why use ModelAdmin? Provides better organization, filtering, search, and display options
compared to basic admin.site.register().
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserProfile, Category, Product, Order, OrderItem,
    ProductReview, Wishlist, NewsletterSubscriber
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for user profiles.
    
    list_display: Fields shown in the list view
    search_fields: Fields that can be searched
    list_filter: Fields that can be filtered
    """
    list_display = ['user', 'phone', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for product categories."""
    list_display = ['name', 'slug', 'product_count', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}  # Auto-generate slug from name
    readonly_fields = ['created_at']
    
    def product_count(self, obj):
        """Display number of products in this category."""
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for products.
    
    Why prepopulated_fields? Automatically generates slug from name as you type.
    Why list_editable? Allows quick editing of featured/stock directly from list view.
    """
    list_display = ['name', 'category', 'price', 'stock', 'featured', 'created_at', 'image_preview']
    list_filter = ['category', 'featured', 'created_at', 'stock']
    search_fields = ['name', 'description', 'short_description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['featured', 'stock']  # Quick edit from list view
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'featured')
        }),
        ('Description', {
            'fields': ('short_description', 'description')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock')
        }),
        ('Image', {
            'fields': ('image', 'image_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Collapsed by default
        }),
    )
    
    def image_preview(self, obj):
        """Display image thumbnail in admin."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


class OrderItemInline(admin.TabularInline):
    """
    Inline admin for order items.
    
    Why TabularInline? Shows order items in a table within the order admin page.
    This allows viewing order items directly from the order page.
    
    Why readonly? Order items shouldn't be modified after order is placed.
    This preserves order history integrity.
    """
    model = OrderItem
    extra = 0  # Don't show empty forms
    can_delete = False  # Prevent deleting order items
    readonly_fields = ['product', 'quantity', 'price_at_purchase', 'subtotal_display']
    
    def subtotal_display(self, obj):
        """
        Display calculated subtotal in admin.
        
        Why separate method? Can't use model method directly in readonly_fields.
        This wrapper formats the output nicely for admin display.
        """
        if obj.pk:  # Only calculate if object is saved
            subtotal = obj.get_subtotal()
            return f"${subtotal:.2f}"
        return "-"
    subtotal_display.short_description = 'Subtotal'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin interface for orders.
    
    Allows admins to:
    - View order details
    - Change order status (pending -> shipped -> delivered)
    - Update shipping information
    - View order items inline
    """
    list_display = ['id', 'user', 'total_price', 'status', 'item_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email', 'id']
    readonly_fields = ['created_at', 'updated_at', 'total_price']  # Total calculated, shouldn't be edited manually
    inlines = [OrderItemInline]  # Show order items on order page
    
    # Allow editing status directly from list view for quick updates
    list_editable = ['status']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'total_price')
        }),
        ('Shipping', {
            'fields': ('shipping_address', 'phone', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Add actions for bulk status updates
    actions = ['mark_shipped', 'mark_delivered', 'mark_cancelled']
    
    def mark_shipped(self, request, queryset):
        """Admin action to mark selected orders as shipped."""
        updated = queryset.filter(status=Order.STATUS_PENDING).update(status=Order.STATUS_SHIPPED)
        self.message_user(request, f"{updated} order(s) marked as shipped.")
    mark_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_delivered(self, request, queryset):
        """Admin action to mark selected orders as delivered."""
        updated = queryset.filter(status__in=[Order.STATUS_PENDING, Order.STATUS_SHIPPED]).update(status=Order.STATUS_DELIVERED)
        self.message_user(request, f"{updated} order(s) marked as delivered.")
    mark_delivered.short_description = "Mark selected orders as delivered"
    
    def mark_cancelled(self, request, queryset):
        """Admin action to mark selected orders as cancelled."""
        updated = queryset.filter(status=Order.STATUS_PENDING).update(status=Order.STATUS_CANCELLED)
        self.message_user(request, f"{updated} order(s) marked as cancelled.")
    mark_cancelled.short_description = "Mark selected orders as cancelled"
    
    def item_count(self, obj):
        """Display number of items in order."""
        return obj.items.count()
    item_count.short_description = 'Items'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin interface for order items."""
    list_display = ['order', 'product', 'quantity', 'price_at_purchase', 'get_subtotal']
    list_filter = ['order__status', 'order__created_at']
    search_fields = ['order__id', 'product__name']
    readonly_fields = ['get_subtotal']
    
    def get_subtotal(self, obj):
        """Display calculated subtotal."""
        return f"${obj.get_subtotal():.2f}"
    get_subtotal.short_description = 'Subtotal'


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """Admin interface for product reviews."""
    list_display = ['product', 'user', 'rating', 'verified_purchase', 'helpful_count', 'created_at']
    list_filter = ['rating', 'verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__username', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('product', 'user', 'rating', 'title', 'comment')
        }),
        ('Verification', {
            'fields': ('verified_purchase', 'helpful_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """Admin interface for wishlist items."""
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['created_at']


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Admin interface for newsletter subscribers."""
    list_display = ['email', 'subscribed', 'subscribed_at', 'unsubscribed_at']
    list_filter = ['subscribed', 'subscribed_at']
    search_fields = ['email']
    readonly_fields = ['subscribed_at', 'unsubscribed_at']
    
    actions = ['mark_subscribed', 'mark_unsubscribed']
    
    def mark_subscribed(self, request, queryset):
        """Admin action to mark selected subscribers as subscribed."""
        queryset.update(subscribed=True, unsubscribed_at=None)
        self.message_user(request, f"{queryset.count()} subscribers marked as subscribed.")
    mark_subscribed.short_description = "Mark selected as subscribed"
    
    def mark_unsubscribed(self, request, queryset):
        """Admin action to mark selected subscribers as unsubscribed."""
        from django.utils import timezone
        queryset.update(subscribed=False, unsubscribed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} subscribers marked as unsubscribed.")
    mark_unsubscribed.short_description = "Mark selected as unsubscribed"

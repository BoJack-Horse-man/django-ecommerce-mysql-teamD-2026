from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify

from django.conf import settings



    

"""
Django Models for E-Commerce Application

This module defines all database models for the e-commerce store including:
- UserProfile: Extended user information with profile photo
- Category: Product categories for organization
- Product: Main product model with pricing, stock, and images
- Order: Customer orders with status tracking
- OrderItem: Individual items within an order
- ProductReview: Customer reviews and ratings for products
- Wishlist: User wishlist/saved items
- NewsletterSubscriber: Email subscription management
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

# Get the User model - using get_user_model() instead of importing User directly
# This makes the code more flexible if we ever need to use a custom user model
User = get_user_model()


class UserProfile(models.Model):
    """
    Extended user profile model to store additional user information.
    
    Why OneToOneField? Each user can have exactly one profile, and if a user is deleted,
    their profile should be deleted too (CASCADE). This is a common pattern in Django.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,  # Delete profile if user is deleted
        related_name='profile'  # Access via user.profile
    )
    photo = models.ImageField(
        upload_to='users/',  # Files stored in media/users/
        blank=True,  # Not required
        null=True  # Can be NULL in database
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """String representation for admin panel and debugging."""
        return f"{self.user.username}'s Profile"


class Category(models.Model):
    """
    Product category model for organizing products.
    
    Why use slug? Slugs create SEO-friendly URLs (e.g., /electronics/ instead of /category/1/).
    The slug is auto-generated from the name if not provided, making URLs readable and shareable.
    """
    name = models.CharField(max_length=255, unique=True)  # Category name must be unique
    slug = models.SlugField(
        max_length=255, 
        unique=True,  # Ensures unique URLs
        blank=True  # Auto-generated if not provided
    )
    description = models.TextField(blank=True)  # Optional category description
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "categories"  # Correct plural form in admin
        ordering = ['name']  # Default ordering by name

    def __str__(self) -> str:
        """String representation for admin panel."""
        return self.name

    def save(self, *args, **kwargs):
        """
        Override save to auto-generate slug from name.
        
        Why override save? This ensures every category has a slug even if admin forgets to set one.
        slugify() converts "Electronics & Gadgets" to "electronics-gadgets".
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Main product model representing items for sale.
    
    Key design decisions:
    - DecimalField for price: Prevents floating-point errors in financial calculations
    - ForeignKey to Category: Products belong to one category, categories can have many products
    - CASCADE delete: If category is deleted, products are deleted (business logic decision)
    - PositiveIntegerField for stock: Can't have negative stock
    """
    name = models.CharField(max_length=255)  # Product name
    slug = models.SlugField(
        max_length=255, 
        unique=True,  # Each product needs unique URL
        blank=True  # Auto-generated if not provided
    )
    description = models.TextField(blank=True)  # Full product description
    short_description = models.CharField(max_length=200, blank=True)  # Brief description for listings
    price = models.DecimalField(
        max_digits=10,  # Up to 99,999,999.99
        decimal_places=2,  # Always 2 decimal places
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal('0.01'))]  # Price must be at least $0.01
    )
    stock = models.PositiveIntegerField(
        default=0,  # Start with 0 stock
        validators=[MinValueValidator(0)]  # Can't be negative
    )
    image = models.ImageField(
        upload_to='products/',  # Files stored in media/products/
        blank=True, 
        null=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,  # Delete product if category deleted
        related_name="products"  # Access via category.products.all()
    )
    featured = models.BooleanField(
        default=False,  # For featured products on homepage
        help_text="Featured products appear on the homepage"
    )
    created_at = models.DateTimeField(auto_now_add=True)  # Auto-set on creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto-update on save

    class Meta:
        ordering = ['name']  # Default ordering
        indexes = [
            models.Index(fields=['category', 'featured']),  # Database index for faster queries
            models.Index(fields=['-created_at']),  # For newest products
        ]

    def __str__(self) -> str:
        """String representation for admin panel."""
        return self.name

    def save(self, *args, **kwargs):
        """
        Override save to auto-generate slug.
        
        Why? Ensures every product has a URL-friendly slug automatically.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def is_in_stock(self):
        """Helper method to check if product is available."""
        return self.stock > 0
    
    def get_average_rating(self):
        """Calculate average rating from all reviews."""
        reviews = self.reviews.all()
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0.0


class Order(models.Model):
    """
    Order model to track customer purchases.
    
    Design decisions:
    - Store total_price: Prices may change, so we save the price at time of purchase
    - Status choices: Track order lifecycle (pending -> shipped -> delivered)
    - CASCADE delete: If user deleted, orders deleted (may want to change to SET_NULL in production)
    """
    # Status constants - using string constants prevents typos
    STATUS_PENDING = "pending"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # Delete orders if user deleted
        related_name="orders"  # Access via user.orders.all()
    )
    total_price = models.DecimalField(
        max_digits=12,  # Up to 999,999,999,999.99
        decimal_places=2,
        default=Decimal("0.00")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,  # Dropdown in admin
        default=STATUS_PENDING
    )
    shipping_address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True, help_text="Special delivery instructions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Newest first
        indexes = [
            models.Index(fields=['user', '-created_at']),  # Fast user order queries
            models.Index(fields=['status']),  # Fast status filtering
        ]

    def __str__(self) -> str:
        """String representation for admin panel."""
        return f"Order #{self.pk} - {self.user.username}"
    
    def get_status_display_class(self):
        """Return Bootstrap class for status badge color."""
        status_classes = {
            self.STATUS_PENDING: 'warning',
            self.STATUS_SHIPPED: 'info',
            self.STATUS_DELIVERED: 'success',
            self.STATUS_CANCELLED: 'danger',
        }
        return status_classes.get(self.status, 'secondary')


class OrderItem(models.Model):
    """
    Individual items within an order.
    
    Why PROTECT on product delete? If a product is deleted, we don't want to lose
    historical order data. PROTECT prevents deletion and raises ProtectedError.
    This is important for accounting and customer service.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,  # Delete items if order deleted
        related_name="items"  # Access via order.items.all()
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,  # Prevent deletion if product in orders
        related_name="order_items"  # Access via product.order_items.all()
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]  # Must be at least 1
    )
    price_at_purchase = models.DecimalField(
        max_digits=10, 
        decimal_places=2
    )
    # Why store price_at_purchase? Product prices may change, but we need to know
    # what the customer actually paid at the time of purchase.

    class Meta:
        ordering = ['product__name']  # Order by product name

    def __str__(self) -> str:
        """String representation for admin panel."""
        return f"{self.product.name} x {self.quantity}"
    
    def get_subtotal(self):
        """Calculate subtotal for this line item."""
        return self.quantity * self.price_at_purchase


class ProductReview(models.Model):
    """
    Customer reviews and ratings for products.
    
    This allows customers to leave feedback and helps other customers make decisions.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,  # Delete reviews if product deleted
        related_name="reviews"  # Access via product.reviews.all()
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # Delete reviews if user deleted
        related_name="reviews"  # Access via user.reviews.all()
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],  # 1-5 stars
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()
    verified_purchase = models.BooleanField(
        default=False,  # Mark as verified if user actually bought the product
        help_text="True if reviewer purchased this product"
    )
    helpful_count = models.PositiveIntegerField(default=0)  # Track helpful votes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']  # Newest reviews first
        unique_together = ['product', 'user']  # One review per user per product
        indexes = [
            models.Index(fields=['product', '-rating']),  # Fast product review queries
        ]
    
    def __str__(self):
        """String representation for admin panel."""
        return f"{self.user.username}'s review of {self.product.name}"


class Wishlist(models.Model):
    """
    User wishlist to save products for later.
    
    Many-to-many relationship: Users can have many products, products can be in many wishlists.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # Delete wishlist if user deleted
        related_name="wishlist_items"  # Access via user.wishlist_items.all()
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,  # Remove from wishlist if product deleted
        related_name="wishlisted_by"  # Access via product.wishlisted_by.all()
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']  # Prevent duplicate entries
        ordering = ['-created_at']  # Most recently added first
    
    def __str__(self):
        """String representation for admin panel."""
        return f"{self.user.username} - {self.product.name}"


class NewsletterSubscriber(models.Model):
    """
    Newsletter subscription management.
    
    Stores email addresses for marketing campaigns and updates.
    """
    email = models.EmailField(unique=True)  # Each email can only subscribe once
    subscribed = models.BooleanField(default=True)  # Allow unsubscribing
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-subscribed_at']
    
    def __str__(self):
        """String representation for admin panel."""
        return self.email
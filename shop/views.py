"""
Django Views for E-Commerce Application

This module contains all view functions that handle HTTP requests and responses.
Views are organized by functionality:
- Helper Functions: Cart management utilities
- Home View: Landing page
- Product Views: Product listing, detail, search, filtering
- Cart Views: Add, update, remove items from cart
- Checkout & Order Views: Order processing and confirmation
- User Profile & Auth Views: Registration, login, profile management
- Additional Features: Reviews, wishlist, contact, etc.

Key design patterns used:
- Session-based cart: Stored in request.session for guest users
- @login_required decorator: Protects views that require authentication
- get_object_or_404: Returns 404 if object not found (better UX than 500 error)
- transaction.atomic(): Ensures database operations are all-or-nothing
"""

from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import (
    Product, Category, Order, OrderItem, UserProfile,
    ProductReview, Wishlist, NewsletterSubscriber
)
from .forms import UserProfileForm, ContactForm, ReviewForm, NewsletterForm

# === Helper Functions ===

def get_cart(request):
    """
    Get or initialize cart from session.
    
    Why session-based cart?
    - Works for both authenticated and guest users
    - No database queries needed for cart operations
    - Automatically cleared when session expires
    
    Returns: dict with product_id (str) as key and quantity (int) as value
    Example: {'1': 2, '5': 1} means 2 of product 1, 1 of product 5
    """
    cart = request.session.get('cart', {})
    # Safety check: ensure cart is always a dict
    # This prevents errors if session data gets corrupted
    if not isinstance(cart, dict):
        cart = {}
        request.session['cart'] = cart
        request.session.modified = True
    return cart

def save_cart(request, cart):
    """
    Save cart to session.
    
    Why set modified=True?
    Django only saves session if it detects changes. Since we're modifying
    a nested dict (cart), we need to explicitly mark session as modified.
    """
    request.session['cart'] = cart
    request.session.modified = True  # Important: tells Django to save session


def get_recently_viewed(request, limit=5):
    """
    Get recently viewed products from session.
    
    Why session-based? Simple, no database overhead, works for all users.
    Returns list of product IDs.
    """
    return request.session.get('recently_viewed', [])[:limit]

# === Home View ===

def home(request):
    """
    Professional home page with featured products and information.
    
    Why filter by stock > 0? Don't show out-of-stock products on homepage.
    Why limit to 6? Keeps homepage fast and not overwhelming.
    Why order by -created_at? Show newest products first (most relevant).
    """
    # Get featured products that are in stock, limit to 6 for homepage
    featured_products = Product.objects.filter(
        stock__gt=0,
        featured=True  # Only show products marked as featured
    ).order_by('-created_at')[:6]
    
    # If no featured products, fall back to newest in-stock products
    if not featured_products.exists():
        featured_products = Product.objects.filter(stock__gt=0).order_by('-created_at')[:6]
    
    # Get categories for homepage display
    categories = Category.objects.all()[:6]
    
    # Statistics for homepage
    total_products = Product.objects.filter(stock__gt=0).count()
    total_categories = Category.objects.count()
    
    # Get recently viewed products (if user has any)
    recently_viewed_ids = get_recently_viewed(request, limit=4)
    recently_viewed = Product.objects.filter(
        id__in=recently_viewed_ids,
        stock__gt=0
    ) if recently_viewed_ids else []
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'total_products': total_products,
        'total_categories': total_categories,
        'recently_viewed': recently_viewed,
    }
    return render(request, 'shop/home.html', context)

# === Product Views ===

def product_list(request):
    """
    Product listing page with search, filtering, sorting, and pagination.
    
    Features:
    - Search by name or description (case-insensitive)
    - Filter by category
    - Filter by price range
    - Sort by price, name, or date
    - Pagination (12 products per page)
    
    Why Q objects? Allows complex OR queries (search in name OR description).
    Why .strip()? Removes whitespace that users might accidentally add.
    Why try/except for price? Gracefully handle invalid input instead of crashing.
    """
    # Start with all products
    products = Product.objects.filter(stock__gt=0)  # Only show in-stock products
    
    # Search functionality - search in product name or description
    query = (request.GET.get('q') or '').strip()
    if query:
        # Q objects allow OR queries: name contains query OR description contains query
        # icontains = case-insensitive contains (more user-friendly)
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(short_description__icontains=query)
        )
    
    # Category filter
    category_id = (request.GET.get('category') or '').strip()
    if category_id and category_id.isdigit():
        products = products.filter(category_id=int(category_id))
    
    # Price range filter
    min_price = (request.GET.get('min_price') or '').strip()
    max_price = (request.GET.get('max_price') or '').strip()
    
    if min_price:
        try:
            # gte = greater than or equal to
            products = products.filter(price__gte=Decimal(min_price))
        except (ValueError, InvalidOperation):
            messages.warning(request, "Invalid minimum price.")
    
    if max_price:
        try:
            # lte = less than or equal to
            products = products.filter(price__lte=Decimal(max_price))
        except (ValueError, InvalidOperation):
            messages.warning(request, "Invalid maximum price.")
    
    # Sorting functionality
    sort_by = request.GET.get('sort', 'name')  # Default sort by name
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'rating':
        # Sort by average rating (requires annotation)
        products = products.annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-avg_rating', 'name')
    
    # Pagination: 12 products per page
    # Why 12? Good balance: 3x4 or 4x3 grid layouts, not too many to load
    paginator = Paginator(products, 12)
    page = request.GET.get('page', 1)
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        products_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        products_page = paginator.page(paginator.num_pages)

    context = {
        'products': products_page,
        'query': query,
        'categories': Category.objects.all(),
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    return render(request, 'shop/product_list.html', context)

def product_detail(request, slug):
    """
    Product detail page showing full product information.
    
    Features:
    - Full product details
    - Related products (same category)
    - Product reviews and ratings
    - Add to cart functionality
    - Add to wishlist functionality
    - Track recently viewed
    
    Why use slug instead of ID? SEO-friendly URLs and more readable.
    Example: /laptop-pro-2024/ vs /123/
    """
    # Get product or return 404 if not found
    product = get_object_or_404(Product, slug=slug)
    
    # Track recently viewed products in session
    # Why? Helps show "recently viewed" on homepage
    recently_viewed = request.session.get('recently_viewed', [])
    if product.id not in recently_viewed:
        recently_viewed.insert(0, product.id)  # Add to beginning
        recently_viewed = recently_viewed[:10]  # Keep only last 10
        request.session['recently_viewed'] = recently_viewed
        request.session.modified = True
    
    # Get related products (same category, exclude current product)
    related_products = Product.objects.filter(
        category=product.category,
        stock__gt=0
    ).exclude(id=product.id)[:4]
    
    # Get reviews with ratings
    reviews = ProductReview.objects.filter(product=product).select_related('user')[:10]
    review_stats = ProductReview.objects.filter(product=product).aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id')
    )
    
    # Check if user has this in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists()
    
    # Check if user can review (has purchased this product)
    can_review = False
    if request.user.is_authenticated:
        can_review = OrderItem.objects.filter(
            order__user=request.user,
            product=product
        ).exists() and not ProductReview.objects.filter(
            user=request.user,
            product=product
        ).exists()
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'review_stats': review_stats,
        'in_wishlist': in_wishlist,
        'can_review': can_review,
    }
    return render(request, 'shop/product_detail.html', context)

# === Cart Views ===

def add_to_cart(request, product_id):
    """
    Add product to shopping cart.
    
    Why POST only? Adding to cart modifies state, should use POST method.
    Why check stock? Prevent adding more items than available.
    Why use string keys? Session stores keys as strings, easier to work with.
    
    Flow:
    1. Get product (404 if not found)
    2. Get quantity from POST data
    3. Get current cart from session
    4. Check available stock (stock - current_qty_in_cart)
    5. Add to cart or show error
    """
    product = get_object_or_404(Product, id=product_id)
    
    # Get quantity from POST, default to 1 if not provided
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1
    
    # Ensure quantity is at least 1
    if quantity < 1:
        quantity = 1

    cart = get_cart(request)
    product_key = str(product.id)  # Session keys are strings
    current_qty = cart.get(product_key, 0)  # How many already in cart

    # Check stock limit - can't add more than available
    # available = total stock - what's already in cart
    available = product.stock - current_qty
    add_qty = min(quantity, max(available, 0))  # Don't add more than available

    if add_qty < 1:
        messages.error(request, f"Only {product.stock} available in stock.")
        return redirect('product_detail', slug=product.slug)

    # Update cart: add new quantity to existing quantity
    cart[product_key] = current_qty + add_qty
    save_cart(request, cart)

    messages.success(request, f"{add_qty} × {product.name} added to cart!")
    return redirect('product_detail', slug=product.slug)

def cart_summary(request):
    """
    Display shopping cart summary with all items and total.
    
    Why validate cart items? Products might be deleted or stock might change.
    Why remove invalid items? Better UX than showing errors for deleted products.
    Why use Decimal? Prevents floating-point errors in financial calculations.
    """
    cart = get_cart(request)
    cart_items = []
    total = Decimal('0.00')
    needs_save = False

    # Process each item in cart
    # Use list(cart.items()) to avoid "dictionary changed size during iteration" error
    for product_id_str, qty in list(cart.items()):
        try:
            product = Product.objects.get(id=int(product_id_str))
            
            # Validate quantity: must be positive and not exceed stock
            if qty < 1 or qty > product.stock:
                raise ValueError("Invalid quantity")
            
            # Calculate subtotal for this item
            subtotal = product.price * qty
            total += subtotal
            
            cart_items.append({
                'product': product,
                'quantity': qty,
                'subtotal': subtotal,
            })
        except (ValueError, Product.DoesNotExist):
            # Product was deleted or quantity invalid - remove from cart
            cart.pop(product_id_str, None)
            needs_save = True

    # Save cart if we removed invalid items
    if needs_save:
        save_cart(request, cart)

    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': sum(item['quantity'] for item in cart_items),
    }
    return render(request, 'shop/cart_summary.html', context)

def cart_update(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        try:
            quantity = int(request.POST.get('quantity', 0))
        except (TypeError, ValueError):
            quantity = 0

        cart = get_cart(request)
        product_key = str(product_id)

        if quantity > 0:
            if quantity > product.stock:
                messages.error(request, f"Only {product.stock} available.")
            else:
                cart[product_key] = quantity
                messages.success(request, f"Updated {product.name} quantity.")
        else:
            cart.pop(product_key, None)
            messages.success(request, f"Removed {product.name} from cart.")

        save_cart(request, cart)

    return redirect('cart_summary')

# === Checkout & Order Views ===

@login_required
def checkout(request):
    """
    Process checkout and create order.
    
    Why @login_required? Users must be logged in to checkout.
    Why transaction.atomic()? Ensures all-or-nothing: either all items are processed
    or none are. Prevents partial orders if something fails.
    
    Flow:
    1. Check cart is not empty
    2. Start database transaction
    3. Create order
    4. For each cart item:
       - Check stock availability
       - Create order item
       - Reduce product stock
    5. Calculate and save total
    6. Clear cart
    7. Redirect to confirmation
    
    Why reduce stock here? Prevents overselling if multiple users checkout simultaneously.
    In production, consider using select_for_update() for row-level locking.
    """
    cart = get_cart(request)
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_summary')

    # Use transaction to ensure atomicity
    # If any step fails, all changes are rolled back
    with transaction.atomic():
        total = Decimal('0.00')
        
        # Create order first (we'll update total_price later)
        order = Order.objects.create(
            user=request.user,
            total_price=Decimal('0.00'),  # Temporary, will update
            status=Order.STATUS_PENDING
        )

        # Process each item in cart
        for product_id_str, quantity in list(cart.items()):
            product_id = int(product_id_str)
            product = get_object_or_404(Product, id=product_id)

            # Final stock check before creating order
            if quantity > product.stock:
                messages.error(request, f"Not enough stock for {product.name}.")
                order.delete()  # Rollback: delete the order
                return redirect('cart_summary')

            # Calculate subtotal
            subtotal = product.price * quantity
            total += subtotal

            # Create order item with price at time of purchase
            # Why store price_at_purchase? Product prices may change later
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_purchase=product.price
            )

            # Reduce stock (critical: happens inside transaction)
            product.stock -= quantity
            product.save()

        # Update order with final total
        order.total_price = total
        order.save()

    # Clear cart after successful order
    # Only clear if we got here (transaction succeeded)
    request.session['cart'] = {}
    request.session.modified = True

    messages.success(request, f"Order #{order.pk} placed successfully!")
    return redirect('order_confirmation', order_id=order.pk)

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = []
    for item in order.items.select_related('product'):
        items.append({
            'product': item.product,
            'quantity': item.quantity,
            'price_at_purchase': item.price_at_purchase,
            'subtotal': item.quantity * item.price_at_purchase,
        })
    return render(request, 'shop/order_confirmation.html', {
        'order': order,
        'items': items,
        'total': order.total_price,
    })

# === User Profile & Auth Views ===

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome.")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def user_profile(request):
    """
    User profile page showing profile info, orders, and wishlist.
    
    Why @login_required? Users should only see their own profile.
    Why get_or_create? Automatically creates profile if it doesn't exist.
    """
    # Get or create user profile (creates if first time accessing)
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=profile)

    # Get user's orders (newest first)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # Get user's wishlist
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')[:10]
    
    context = {
        'profile': profile,
        'form': form,
        'orders': orders,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'shop/user_profile.html', context)
@login_required
def fake_pay(request, order_id):
    """
    Simulate payment processing (for demo purposes).
    
    In production, this would integrate with payment gateways like Stripe, PayPal, etc.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == Order.STATUS_PENDING:
        order.status = Order.STATUS_SHIPPED  # simulation
        order.save()
        messages.success(request, "Payment successful (simulation)! Order is now processing.")
    else:
        messages.info(request, "Order already processed.")
    return redirect('order_confirmation', order_id=order.pk)


# === Wishlist Views ===

@login_required
@require_POST
def add_to_wishlist(request, product_id):
    """
    Add product to user's wishlist.
    
    Why @require_POST? Modifying data should use POST method.
    Why get_or_create? Prevents duplicate entries (also handled by unique_together in model).
    """
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        messages.success(request, f"{product.name} added to wishlist!")
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")
    
    return redirect('product_detail', slug=product.slug)


@login_required
@require_POST
def remove_from_wishlist(request, product_id):
    """Remove product from user's wishlist."""
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f"{product.name} removed from wishlist.")
    return redirect('product_detail', slug=product.slug)


# === Review Views ===

@login_required
def add_review(request, product_id):
    """
    Add product review (only if user purchased the product).
    
    Why check purchase? Ensures reviews are from verified customers.
    Why unique_together? One review per user per product (enforced in model).
    """
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user purchased this product
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        product=product
    ).exists()
    
    if not has_purchased:
        messages.error(request, "You must purchase this product before reviewing it.")
        return redirect('product_detail', slug=product.slug)
    
    # Check if user already reviewed
    if ProductReview.objects.filter(user=request.user, product=product).exists():
        messages.error(request, "You have already reviewed this product.")
        return redirect('product_detail', slug=product.slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.verified_purchase = True  # User purchased it
            review.save()
            messages.success(request, "Thank you for your review!")
            return redirect('product_detail', slug=product.slug)
    else:
        form = ReviewForm()
    
    return render(request, 'shop/add_review.html', {
        'form': form,
        'product': product
    })


# === Contact & Info Pages ===

def contact_us(request):
    """
    Contact us page with form submission.
    
    In production, this would send emails using Django's email backend.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # In production: send email to admin
            # from django.core.mail import send_mail
            # send_mail(...)
            
            messages.success(request, "Thank you for contacting us! We'll get back to you soon.")
            return redirect('contact_us')
    else:
        form = ContactForm()
    
    return render(request, 'shop/contact_us.html', {'form': form})


def about_us(request):
    """About us page with company information."""
    return render(request, 'shop/about_us.html')


def faq(request):
    """Frequently Asked Questions page."""
    faqs = [
        {
            'question': 'How do I place an order?',
            'answer': 'Browse our products, add items to cart, and proceed to checkout. You must be logged in to complete your purchase.'
        },
        {
            'question': 'What payment methods do you accept?',
            'answer': 'Currently, we accept all major credit cards. Payment processing is simulated for demo purposes.'
        },
        {
            'question': 'How long does shipping take?',
            'answer': 'Standard shipping typically takes 5-7 business days. Express shipping options are available at checkout.'
        },
        {
            'question': 'Can I return or exchange items?',
            'answer': 'Yes! You can return items within 30 days of purchase for a full refund. Items must be in original condition.'
        },
        {
            'question': 'How do I track my order?',
            'answer': 'Once your order ships, you will receive a tracking number via email. You can also view order status in your profile.'
        },
    ]
    return render(request, 'shop/faq.html', {'faqs': faqs})


# === Newsletter ===

def newsletter_subscribe(request):
    """
    Newsletter subscription endpoint.
    
    Can be called via AJAX or regular form submission.
    """
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            subscriber, created = NewsletterSubscriber.objects.get_or_create(
                email=email,
                defaults={'subscribed': True}
            )
            
            if not created and not subscriber.subscribed:
                # Resubscribe
                subscriber.subscribed = True
                subscriber.unsubscribed_at = None
                subscriber.save()
                created = True
            
            if created:
                messages.success(request, "Successfully subscribed to our newsletter!")
            else:
                messages.info(request, "You are already subscribed to our newsletter.")
        else:
            messages.error(request, "Please enter a valid email address.")
    
    # Redirect back to referrer or home
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@require_POST
def newsletter_unsubscribe(request):
    """Unsubscribe from newsletter."""
    email = request.POST.get('email', '').strip()
    if email:
        NewsletterSubscriber.objects.filter(email=email).update(
            subscribed=False
        )
        messages.success(request, "You have been unsubscribed from our newsletter.")
    return redirect('home')
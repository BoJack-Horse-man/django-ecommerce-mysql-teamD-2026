from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, Category  # Category was missing!
from django.db.models import Q

# Helper functions
def get_cart(request):
    """Get or initialize cart from session"""
    if 'cart' not in request.session:
        request.session['cart'] = {}
    return request.session['cart']

def save_cart(request, cart):
    """Save cart to session"""
    request.session['cart'] = cart
    request.session.modified = True

# Product list
def product_list(request):
    products = Product.objects.all()
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if category_id and category_id.isdigit():
        products = products.filter(category_id=category_id)

    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except Exception:
            messages.warning(request, "Invalid minimum price filter.")

    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except Exception:
            messages.warning(request, "Invalid maximum price filter.")

    context = {
        'products': products,
        'query': query,
        'categories': Category.objects.all(),
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'shop/product_list.html', context)

# Product detail
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'shop/product_detail.html', {'product': product})

# Add to cart
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    cart = get_cart(request)
    product_key = str(product.id)
    current_quantity = cart.get(product_key, 0)

    if quantity + current_quantity > product.stock:
        messages.error(request, f"Only {product.stock} available in stock.")
        return redirect('product_detail', slug=product.slug)

    cart[product_key] = current_quantity + quantity
    save_cart(request, cart)

    messages.success(request, f"{quantity} × {product.name} added to cart!")
    return redirect('product_detail', slug=product.slug)

# Cart summary
def cart_summary(request):
    cart = get_cart(request)
    cart_items = []
    total = Decimal('0.00')
    update_cart = False

    for product_id_str, quantity in list(cart.items()):
        try:
            product_id = int(product_id_str)
            product = Product.objects.get(id=product_id)
            subtotal = product.price * quantity
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })
        except (ValueError, Product.DoesNotExist):
            cart.pop(product_id_str, None)
            update_cart = True

    if update_cart:
        save_cart(request, cart)

    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': sum(cart.values()),
    }
    return render(request, 'shop/cart_summary.html', context)

# Update or delete cart item
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
            if product_key in cart:
                del cart[product_key]
                messages.success(request, f"Removed {product.name} from cart.")

        save_cart(request, cart)

    return redirect('cart_summary')
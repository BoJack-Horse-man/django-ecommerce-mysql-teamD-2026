from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, Category, Order, OrderItem
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.db import transaction

def get_cart(request):
    """Get or initialize cart from session"""
    cart = request.session.get('cart')
    if not isinstance(cart, dict):
        cart = {}
        request.session['cart'] = cart
        request.session.modified = True
    return cart

def save_cart(request, cart):
    """Save cart to session"""
    request.session['cart'] = cart
    request.session.modified = True

def product_list(request):
    products = Product.objects.all()
    query = (request.GET.get('q') or '').strip()
    category_id = (request.GET.get('category') or '').strip()
    min_price = (request.GET.get('min_price') or '').strip()
    max_price = (request.GET.get('max_price') or '').strip()

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id and category_id.isdigit():
        products = products.filter(category_id=int(category_id))
    if min_price:
        try:
            min_price_decimal = Decimal(min_price)
            products = products.filter(price__gte=min_price_decimal)
        except Exception:
            messages.warning(request, "Invalid minimum price filter.")
    if max_price:
        try:
            max_price_decimal = Decimal(max_price)
            products = products.filter(price__lte=max_price_decimal)
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

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'shop/product_detail.html', {'product': product})

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
    # Prevent exceeding stock
    addable_quantity = min(quantity, max(product.stock - current_quantity, 0))
    if addable_quantity < 1:
        messages.error(request, f"Only {product.stock} available in stock.")
        return redirect('product_detail', slug=product.slug)

    cart[product_key] = current_quantity + addable_quantity
    save_cart(request, cart)
    messages.success(request, f"{addable_quantity} × {product.name} added to cart!")
    return redirect('product_detail', slug=product.slug)

def cart_summary(request):
    cart = get_cart(request)
    cart_items = []
    total = Decimal('0.00')
    update_cart = False

    for product_id_str, quantity in list(cart.items()):
        try:
            product_id = int(product_id_str)
            product = Product.objects.get(id=product_id)
            if quantity < 1:
                raise ValueError  # Remove invalid (zero/negative) entries
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


@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart or sum(cart.values()) == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_summary')

    with transaction.atomic():
        total = Decimal('0.00')
        order = Order.objects.create(
            user=request.user,
            total_price=Decimal('0.00'),
            status=Order.STATUS_PENDING
        )
        products_to_update = []
        for product_id_str, quantity in list(cart.items()):
            try:
                product_id = int(product_id_str)
                # Lock row for update during transaction
                product = Product.objects.select_for_update().get(id=product_id)
            except (ValueError, Product.DoesNotExist):
                messages.error(request, "A product in your cart no longer exists.")
                order.delete()
                return redirect('cart_summary')

            if quantity > product.stock:
                messages.error(request, f"Not enough stock for {product.name} (only {product.stock} left).")
                order.delete()
                return redirect('cart_summary')

            if quantity < 1:
                continue  # Skip invalid quantity

            subtotal = product.price * quantity
            total += subtotal

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_purchase=product.price
            )

            # Reduce stock
            product.stock -= quantity
            products_to_update.append(product)

        if not products_to_update:
            messages.warning(request, "Your cart is invalid or empty.")
            order.delete()
            return redirect('cart_summary')

        Product.objects.bulk_update(products_to_update, ['stock'])
        order.total_price = total
        order.save()

        # Clear cart
        request.session['cart'] = {}
        request.session.modified = True

    messages.success(request, f"Order #{order.pk} placed successfully!")
    return redirect('order_confirmation', order_id=order.pk)

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
    context = {
        'order': order,
        'items': items,
        'total': order.total_price,
    }
    return render(request, 'shop/order_confirmation.html', context)
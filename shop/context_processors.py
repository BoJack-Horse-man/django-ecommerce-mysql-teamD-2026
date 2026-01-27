"""
Context Processors for E-Commerce Application

Context processors make data available to ALL templates automatically.
This is useful for data that needs to be displayed on every page (like cart count).

Why use context processors instead of adding to each view?
- DRY principle: Don't repeat yourself
- Cart count needed in navbar on every page
- Centralized logic for cart calculation

To use: Add to TEMPLATES['OPTIONS']['context_processors'] in settings.py
"""

def cart_count(request):
    """
    Calculate total number of items in shopping cart.
    
    This function runs on every request and makes 'cart_count' available
    in all templates. This is why the cart count appears in the navbar
    on every page without needing to add it to each view's context.
    
    Returns: dict with 'cart_count' key containing total items
    """
    cart = request.session.get('cart', {})
    
    # Safety check: ensure cart is always a dict
    # Prevents errors if session data gets corrupted
    if not isinstance(cart, dict):
        cart = {}
    
    # Sum all quantities in the cart
    # Cart structure: {'product_id': quantity, ...}
    # Example: {'1': 2, '5': 1} = 3 total items
    total_items = sum(cart.values()) if cart else 0
    
    return {'cart_count': total_items}


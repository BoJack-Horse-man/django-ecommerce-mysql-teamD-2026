Mental Execution & Curator Review (AI Native Style)
As per the rubric,  must perform mental execution on every non-template line of AI-generated code. This means explaining in natural language:

Business logic
Exception paths
Potential side effects
Any hallucinations or issues (and corrections)

Category model
name: CharField(unique=True) – Ensures no duplicate categories.
slug: SlugField(unique=True) – URL-friendly identifier.
description: TextField(blank=True) – Optional field, no validation needed.
save() override: If slug is empty, auto-generates from name using slugify.
Business logic: Prevents manual slug errors, ensures consistency.
Exception path: If name is empty → slugify('') → empty slug → save fails due to unique=True (IntegrityError).
Side effect: Changing name after creation won't auto-update slug (good – prevents breaking existing URLs).

__str__: Returns name – clear for admin panel and debugging.

Product model
price: DecimalField(max_digits=10, decimal_places=2) – Precise money handling (no floating point issues).
stock: PositiveIntegerField(default=0) – Can't be negative.
category: ForeignKey(on_delete=CASCADE) – Deleting category deletes all products (business decision – common in e-commerce).
save(): Same slug logic as Category.
Business logic: Consistent URLs for products.
Exception: Name change doesn't update slug (same as above).

__str__: Name – good.

Order model
user: ForeignKey to User (CASCADE) – Deleting user deletes orders (typical).
total_price: DecimalField – stores calculated total.
status: CharField with choices – controlled vocabulary.
Default "pending" – good.

__str__: Uses pk and user – useful for admin.

OrderItem model
order: ForeignKey(CASCADE) – Deleting order deletes items.
product: ForeignKey(CASCADE) – Deleting product deletes items (but PROTECT could be better if you want to keep historical orders).
Current CASCADE is fine for simple project.

price_at_purchase: Stores price at time of order – prevents price changes affecting historical orders.
__str__: Product name + quantity – clear.


Potential hallucinations / issues in generated code:

No related_name on some ForeignKeys – minor, but related_name="order_items" on OrderItem.product could be added for reverse queries.
No unique_together or indexes – for performance later (e.g., unique slug per category).
No ordering Meta – e.g., ordering = ['-created_at'] for recent first.
No validation (e.g., price > 0, stock >= 0) – can add in clean() method later.
No image field – optional for now.

# ME.log.md - shop/models.py (2026-01-21)

Code 
[ME] Explanation:
- Forward reference fixed with 'Product' string in ForeignKey → prevents NameError at import time.
- OrderItem.on_delete=PROTECT on product → raises ProtectedError if delete attempted (protects order history).
- Exception path: Deleting product with orders → ProtectedError (intentional).
- Side effect: Price changes after order don't affect history (price_at_purchase snapshot).
- Meta ordering added: Category/Product by name, Order by -created_at.
- No hallucinations after fix.
login/register views + templates
[ME] Explanation:
- UserCreationForm handles password hashing + validation.
- Exception path: Invalid form → error message, no DB change.
- Side effect: Successful register → auto-login + redirect.
- Hallucination: None, matches spec.
user profile view + template
[ME] Explanation:
- Orders filtered by user → secure, no other users' data.
- Exception path: No orders → friendly message.
- Side effect: Poll for status → real-time without WebSockets.
- Hallucination: None.
# Django E-Commerce Project

Team: A

Tech: Django 4.2.16, MySQL (XAMPP), Bootstrap 5, PyMySQL

## Setup
1. Start XAMPP MySQL
2. `python -m venv venv && .\venv\Scripts\Activate.ps1`
3. `pip install -r requirements.txt`
4. `python manage.py migrate`
5. `python manage.py createsuperuser`
6. `python manage.py runserver`

# ME.log.md - 2026-01-27
Implemented customer-facing pages and profile upgrades
[ME] Notes:
- Added password change flow via Django auth views + templates → secure password update with built-in validation. Success redirects to confirmation.
- Built contact, about, FAQ, wishlist, product request, and review submission templates → resolves TemplateDoesNotExist errors and surfaces existing features.
- Product detail now shows ratings, reviews with optional photos, and wishlist add/remove actions → leverages ProductReview data and Wishlist endpoints; uses POST for mutations to avoid CSRF issues.
- Profile page now renders UserUpdateForm + UserProfileForm (photo/phone/address) with separate form_name fields → prevents accidental cross-validation and displays full user info.
- Product requests page uses ProductRequestForm with reference image upload and status list → matches ProductRequest model fields.
- Risk: Navbar “Request Product” only visible to authenticated users; unauthenticated users must log in to access the requests view (login_required). Ensure media storage configured for uploads (profile photos/review images/reference images).

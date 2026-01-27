from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from shop import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='product_list'), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.user_profile, name='user_profile'),

    # Cart & Checkout
    path('cart/', views.cart_summary, name='cart_summary'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('order/<int:order_id>/pay/', views.fake_pay, name='fake_pay'),

    # Product Routes (generic slug MUST be last!)
    path('', views.product_list, name='product_list'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]

# Serve media files during development (only when DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
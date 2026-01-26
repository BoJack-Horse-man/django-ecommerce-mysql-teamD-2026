from .models import UserProfile

admin.site.register(UserProfile)
{% if product.image %}
    <img src="{{ product.image.url }}" alt="{{ product.name }}" class="img-fluid rounded">
{% else %}
    <div class="product-image-placeholder">No image</div>
{% endif %}
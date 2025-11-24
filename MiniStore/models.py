from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

# --- 1. ROLE DEFINITIONS ---
ROLE_CHOICES = (
    ("ADMIN", "Admin"),
    ("SELLER", "Seller"),
    ("CUSTOMER", "Customer"),
)


# --- 2. CATEGORY & PRODUCT MODELS ---
class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("product_list_by_category", args=[self.slug])

class Product(models.Model):
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(upload_to="products/%Y/%m/%d", blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "product"
        verbose_name_plural = "products"

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("product_detail", args=[self.slug])

# --- 3. USER PROFILE ---
class UserProfile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="CUSTOMER")
    
    # --- PERSONAL INFO ---
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)

    # --- SHIPPING ADDRESS ---
    address = models.CharField(max_length=250, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)

    # --- SELLER STATUS FIELD ---
    SELLER_STATUS_CHOICES = (
    ('NONE', 'None'),
    ('PENDING', 'Pending Approval'),
    ('APPROVED', 'Approved'),
    ('CANCELLATION_REQUESTED', 'Cancellation Requested'), 
)
    seller_status = models.CharField(max_length=50, choices=SELLER_STATUS_CHOICES, default='NONE')

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role} - {self.seller_status})"

# --- 4. ORDER MODELS ---
class Order(models.Model):
    user = models.ForeignKey(
        User,
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    # These fields capture the address *at the time of the order*
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"Order {self.id}"

    def get_total_cost(self):
        """Calculate total cost of all items in the order."""
        return sum(item.get_cost() for item in self.items.all())

class OrderItem(models.Model):
    """Tracks the individual items and quantities within a single Order."""
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="order_items", on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self) -> str:
        return f"{self.product.name} ({self.quantity})"

    def get_cost(self):
        """Calculate cost for this item (price * quantity)."""
        return self.price * self.quantity

# --- 5. NOTIFICATIONS ---
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: Link to an order if you want the notification to be clickable
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message}"
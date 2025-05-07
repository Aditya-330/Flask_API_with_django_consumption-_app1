from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Medicine(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='medicines/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='medicines')
    requires_prescription = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    discount_percentage = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    usage_limit = models.PositiveIntegerField(default=1)  # How many times a user can use this code
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and 
            self.valid_from <= now <= self.valid_to
        )

class UserPromoUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    promo = models.ForeignKey(PromoCode, on_delete=models.CASCADE)
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'promo')

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Cart"
    
    def get_total_price(self):
        return sum(item.get_cost() for item in self.items.all())
    
    def get_discount_amount(self):
        if not self.promo_code or not self.promo_code.is_valid():
            return 0
        
        total = self.get_total_price()
        if total < self.promo_code.min_order_value:
            return 0
        
        discount = total * (Decimal(self.promo_code.discount_percentage) / Decimal('100'))
        # discount = total * (self.promo_code.discount_percentage / 100)
        
        if self.promo_code.max_discount_amount:
            return min(discount, self.promo_code.max_discount_amount)
        return discount
    
    def get_final_price(self):
        return self.get_total_price() - self.get_discount_amount()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.medicine.name}"
    
    def get_cost(self):
        return self.medicine.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('upi', 'UPI Payment'),
        ('wallet', 'Digital Wallet'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=10)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at the time of ordering
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.medicine.name}"
    
    def get_cost(self):
        return self.price * self.quantity

class Prescription(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='prescriptions', null=True, blank=True)
    image = models.ImageField(upload_to='prescriptions/')
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Prescription {self.id} - {self.user.username}"
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('seller', 'Seller'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer'
    )

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    bio = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name



class Seller(models.Model):
    user = models.OneToOneField(
        'appreloop.CustomUser',
        on_delete=models.CASCADE,
        related_name='seller_profile'
    )
    shop_name = models.CharField(max_length=150)
    shop_description = models.TextField(blank=True)
    shop_address = models.TextField()
    shop_phone = models.CharField(max_length=15)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.shop_name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )

    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name='products'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Wishlist(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return self.user.username + " - " + self.product.name

class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.product.name} ({self.rating}/5)'
    


class Offer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    offered_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.buyer.username} - {self.product.name}'



class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders'
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.buyer.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )

    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

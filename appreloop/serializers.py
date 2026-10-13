from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAdminUser
from rest_framework import generics
from .models import Review
from .models import Order, OrderItem, Product
from rest_framework.response import Response
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import DonationRequest
from .models import RepairRequest
from .models import *


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'role']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'customer')
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            username=data['username'],
            password=data['password']
        )

        if user is None:
            raise serializers.ValidationError("Invalid username or password")

        if not user.is_active:
            raise serializers.ValidationError("User account is inactive")

        data['user'] = user
        return data


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'user', 'bio', 'city', 'state']
        read_only_fields = ['id', 'user']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = [
            'id',
            'user',
            'shop_name',
            'shop_description',
            'shop_address',
            'shop_phone',
            'is_verified',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'is_verified',
            'created_at',
        ]


class SellerVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ['id', 'shop_name', 'is_verified']
        read_only_fields = ['id', 'shop_name']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class WishlistSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        source='product.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'product', 'product_name', 'product_price', 'created_at']
        read_only_fields = ['id', 'created_at']



class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    rating_stars = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'username', 'product',
            'rating', 'rating_stars', 'comment',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'username',
            'rating_stars', 'created_at', 'updated_at'
        ]


    def get_rating_stars(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value

class OfferSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(
        source='buyer.username',
        read_only=True
    )

    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    class Meta:
        model = Offer
        fields = [
            'id',
            'buyer',
            'buyer_name',
            'product',
            'product_name',
            'offered_price',
            'status',
            'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'quantity',
            'unit_price',
            'subtotal',
        ]
        read_only_fields = ['unit_price', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'buyer',
            'items',
            'total_amount',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'buyer',
            'total_amount',
            'status',
            'created_at',
            'updated_at',
        ]


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_list_create(request):
    if request.method == 'GET':
        orders = Order.objects.filter(
            buyer=request.user
        ).prefetch_related('items__product')

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    items_data = request.data.get('items', [])

    if not isinstance(items_data, list) or not items_data:
        return Response(
            {'error': 'At least one item is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            total = 0
            validated_items = []

            for item in items_data:
                if not isinstance(item, dict):
                    return Response(
                        {'error': 'Each item must be an object.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                product_id = item.get('product')
                quantity = item.get('quantity')

                if (
                    not isinstance(quantity, int)
                    or isinstance(quantity, bool)
                    or quantity <= 0
                ):
                    return Response(
                        {'error': 'Quantity must be a positive integer.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                product = Product.objects.select_for_update().get(
                    pk=product_id
                )

                if product.stock < quantity:
                    return Response(
                        {'error': f'Insufficient stock for {product.name}.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                total += product.price * quantity
                validated_items.append((product, quantity))

            order = Order.objects.create(
                buyer=request.user,
                total_amount=total
            )

            for product, quantity in validated_items:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price
                )

                product.stock -= quantity
                product.save(update_fields=['stock'])

        serializer = OrderSerializer(order)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    except Product.DoesNotExist:
        return Response(
            {'error': 'One or more products were not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    except (ValueError, TypeError):
        return Response(
            {'error': 'Invalid product ID or request data.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class DonationRequestSerializer(serializers.ModelSerializer):
    donor_username = serializers.CharField(
        source='donor.username',
        read_only=True
    )
    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    class Meta:
        model = DonationRequest
        fields = [
            'id',
            'donor',
            'donor_username',
            'product',
            'product_name',
            'message',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'donor',
            'status',
            'created_at',
            'updated_at',
        ]


class PaymentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            'id',
            'user',
            'username',
            'amount',
            'payment_method',
            'payment_status',
            'transaction_id',
            'created_at'
        ]

        read_only_fields = [
            'id',
            'user',
            'username',
            'payment_status',
            'transaction_id',
            'created_at'
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Amount must be greater than zero."
            )
        return value


class ExchangeRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(
        source='requester.username',
        read_only=True
    )

    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    offered_product_name = serializers.CharField(
        source='offered_product.name',
        read_only=True
    )

    class Meta:
        model = ExchangeRequest
        fields = [
            'id',
            'requester',
            'requester_name',
            'product',
            'product_name',
            'offered_product',
            'offered_product_name',
            'message',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'requester',
            'status',
            'created_at',
            'updated_at',
        ]

class RepairRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairRequest
        fields = [
            'id',
            'user',
            'product',
            'issue_description',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'status',
            'created_at',
            'updated_at',
        ]

    def validate_issue_description(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Issue description cannot be empty."
            )
        return value



class RecycleRequestSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = RecycleRequest
        fields = [
            'id',
            'user',
            'username',
            'item_description',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'username',
            'status',
            'created_at',
            'updated_at',
        ]
from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAdminUser
from rest_framework import generics
from .models import Review
from .models import *
from .serializers import *

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
        return '⭐' * obj.rating

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

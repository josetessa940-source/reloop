from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from .models import *
from .serializers import *



class RegisterAPI(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)

            return Response(
                {
                    'message': 'Login successful',
                    'token': token.key,
                    'user_id': user.id,
                    'username': user.username,
                    'role': user.role
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LogoutAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()

        return Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )

class UserDetailsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }, status=status.HTTP_200_OK)



class CreateProfileAPI(generics.CreateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MyProfileAPI(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, created = Profile.objects.get_or_create(
            user=self.request.user
        )
        return profile

class CategoryListCreateAPI(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class CategoryDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class CreateSellerAPI(generics.CreateAPIView):
    serializer_class = SellerSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role != 'seller':
            raise PermissionDenied(
                "Only seller accounts can create a seller profile."
            )

        serializer.save(user=self.request.user)


class MySellerProfileAPI(generics.RetrieveUpdateAPIView):
    serializer_class = SellerSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        if self.request.user.role != 'seller':
            raise PermissionDenied(
                "Only seller accounts can access a seller profile."
            )

        seller, created = Seller.objects.get_or_create(
            user=self.request.user,
            defaults={
                'shop_name': self.request.user.username + "'s Shop",
                'shop_description': '',
                'shop_address': '',
                'shop_phone': '',
            }
        )
        return seller


class SellerVerificationAPI(generics.ListAPIView):
    serializer_class = SellerVerificationSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Seller.objects.filter(is_verified=False)


class SellerVerificationDetailAPI(generics.UpdateAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerVerificationSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['patch', 'put', 'head', 'options']

    def update(self, request, *args, **kwargs):
        seller = self.get_object()
        verified = request.data.get('is_verified')

        if not isinstance(verified, bool):
            return Response(
                {'error': 'is_verified must be true or false.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        seller.is_verified = verified
        seller.save(update_fields=['is_verified'])

        return Response({
            'message': 'Seller verification updated successfully',
            'seller_id': seller.id,
            'is_verified': seller.is_verified,
            'status': 'Verified' if seller.is_verified else 'Pending'
        })

class ProductListCreateAPI(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]


class ProductDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]


# Add product to wishlist
class WishlistCreateView(generics.CreateAPIView):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer


# View wishlist
class WishlistListView(generics.ListAPIView):
    serializer_class = WishlistSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user')
        return Wishlist.objects.filter(user_id=user_id)


# Remove product from wishlist
class WishlistDeleteView(generics.DestroyAPIView):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer


class ReviewListCreateAPI(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(
            product_id=self.request.query_params.get('product')
        ) if self.request.query_params.get('product') else Review.objects.all()

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        existing_review = Review.objects.filter(
            user=request.user,
            product_id=request.data.get('product')
        ).exists()

        if existing_review:
            return Response(
                {'error': 'You have already reviewed this product.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)


class ReviewDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        review = super().get_object()

        if review.user != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied(
                "You can only manage your own reviews."
            )

        return review

# Create and View Offers
class OfferListCreateView(generics.ListCreateAPIView):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer


# Accept Offer
class OfferAcceptView(generics.UpdateAPIView):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer

    def perform_update(self, serializer):
        serializer.save(status='accepted')


# Reject Offer
class OfferRejectView(generics.UpdateAPIView):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer

    def perform_update(self, serializer):
        serializer.save(status='rejected')


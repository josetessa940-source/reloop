from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import DonationRequest,RepairRequest,Pickup,Order,Product
from .serializers import DonationRequestSerializer,RepairRequestSerializer,PickupSerializer
from .models import *
from .serializers import *
from rest_framework.authentication import TokenAuthentication


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
    permission_classes = [IsAuthenticated]


class CategoryDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]


class ProductDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

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
        return [IsAuthenticated()]

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

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_list_create(request):

    if request.method == 'GET':
        orders = (
            Order.objects
            .filter(buyer=request.user)
            .prefetch_related('items__product')
        )

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
            total = Decimal('0.00')
            validated_items = []
            quantities = {}

            
            for item in items_data:
                if not isinstance(item, dict):
                    return Response(
                        {'error': 'Each item must be an object.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                product_id = item.get('product')
                quantity = item.get('quantity')

                if product_id is None:
                    return Response(
                        {'error': 'Product ID is required.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if (
                    not isinstance(quantity, int)
                    or isinstance(quantity, bool)
                    or quantity <= 0
                ):
                    return Response(
                        {'error': 'Quantity must be a positive integer.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                quantities[product_id] = (
                    quantities.get(product_id, 0) + quantity
                )

           
            for product_id, quantity in quantities.items():
                product = Product.objects.get(pk=product_id)

                if product.stock < quantity:
                    return Response(
                        {
                            'error':
                            f'Insufficient stock for {product.name}.'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                total += product.price * quantity
                validated_items.append((product, quantity))

            # Order create cheyyunnu
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

    except (ValueError, TypeError, InvalidOperation):
        return Response(
            {'error': 'Invalid product ID or request data.'},
            status=status.HTTP_400_BAD_REQUEST
        )

# Create Donation Request and View My Donations
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def donation_list_create(request):

    if request.method == 'GET':
        donations = DonationRequest.objects.filter(
            donor=request.user
        ).select_related('product').order_by('-created_at')

        serializer = DonationRequestSerializer(donations, many=True)
        return Response(serializer.data)

    product_id = request.data.get('product')

    if not product_id:
        return Response(
            {'error': 'Product ID is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    product = get_object_or_404(Product, id=product_id)

    # Prevent duplicate active requests for the same product
    existing = DonationRequest.objects.filter(
        donor=request.user,
        product=product,
        status__in=['pending', 'approved']
    ).exists()

    if existing:
        return Response(
            {'error': 'An active donation request already exists for this product.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    donation = DonationRequest.objects.create(
        donor=request.user,
        product=product,
        message=request.data.get('message', '')
    )

    serializer = DonationRequestSerializer(donation)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def donation_detail(request, donation_id):
    donation = get_object_or_404(
        DonationRequest.objects.select_related('product', 'donor'),
        id=donation_id,
        donor=request.user
    )

    serializer = DonationRequestSerializer(donation)
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_donation_status(request, donation_id):
    donation = get_object_or_404(
        DonationRequest,
        id=donation_id
    )

    new_status = request.data.get('status')

    allowed_statuses = ['approved', 'rejected', 'completed']

    if new_status not in allowed_statuses:
        return Response(
            {
                'error': 'Invalid status.',
                'allowed_statuses': allowed_statuses
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if donation.status in ['cancelled', 'completed', 'rejected']:
        return Response(
            {'error': 'This donation request can no longer be updated.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    donation.status = new_status
    donation.save(update_fields=['status', 'updated_at'])

    return Response({
        'message': 'Donation status updated successfully.',
        'donation_id': donation.id,
        'status': donation.status
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_donation(request, donation_id):
    donation = get_object_or_404(
        DonationRequest,
        id=donation_id,
        donor=request.user
    )

    if donation.status != 'pending':
        return Response(
            {'error': 'Only pending donation requests can be cancelled.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    donation.status = 'cancelled'
    donation.save(update_fields=['status', 'updated_at'])

    return Response({
        'message': 'Donation request cancelled successfully.',
        'donation_id': donation.id,
        'status': donation.status
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def payment_list_create(request):
    if request.method == 'GET':
        payments = Payment.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

    serializer = PaymentSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_detail(request, pk):
    try:
        payment = Payment.objects.get(
            pk=pk,
            user=request.user
        )
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = PaymentSerializer(payment)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def payment_status_update(request, pk):
    try:
        payment = Payment.objects.get(
            pk=pk,
            user=request.user
        )
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    new_status = request.data.get('payment_status')

    if new_status not in ['Pending', 'Success', 'Failed']:
        return Response(
            {'error': 'Invalid payment status'},
            status=status.HTTP_400_BAD_REQUEST
        )

    payment.payment_status = new_status
    payment.save()

    serializer = PaymentSerializer(payment)
    return Response(serializer.data)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def exchange_request_list_create(request):

    if request.method == 'GET':
        requests = ExchangeRequest.objects.filter(
            models.Q(requester=request.user) |
            models.Q(product__seller__user=request.user)
        ).select_related(
            'requester', 'product', 'offered_product'
        ).order_by('-created_at')

        serializer = ExchangeRequestSerializer(requests, many=True)
        return Response(serializer.data)

    product_id = request.data.get('product')
    offered_product_id = request.data.get('offered_product')

    if not product_id or not offered_product_id:
        return Response(
            {'error': 'Both product and offered_product are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    product = get_object_or_404(Product, id=product_id)
    offered_product = get_object_or_404(Product, id=offered_product_id)

    if product.id == offered_product.id:
        return Response(
            {'error': 'You cannot exchange a product with itself.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if offered_product.seller.user != request.user:
        return Response(
            {'error': 'You can only offer your own product.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if product.seller.user == request.user:
        return Response(
            {'error': 'You cannot send an exchange request for your own product.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    existing = ExchangeRequest.objects.filter(
        requester=request.user,
        product=product,
        offered_product=offered_product,
        status='pending'
    ).exists()

    if existing:
        return Response(
            {'error': 'An exchange request is already pending.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    exchange_request = ExchangeRequest.objects.create(
        requester=request.user,
        product=product,
        offered_product=offered_product,
        message=request.data.get('message', '')
    )

    serializer = ExchangeRequestSerializer(exchange_request)

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED
    )


# Accept or Reject Exchange Request
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def exchange_request_update_status(request, pk):

    exchange_request = get_object_or_404(
        ExchangeRequest,
        pk=pk
    )

    if exchange_request.product.seller.user != request.user:
        return Response(
            {'error': 'Only the product owner can update this request.'},
            status=status.HTTP_403_FORBIDDEN
        )

    new_status = request.data.get('status')

    if new_status not in ['accepted', 'rejected']:
        return Response(
            {'error': 'Status must be accepted or rejected.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if exchange_request.status != 'pending':
        return Response(
            {'error': 'Only pending requests can be accepted or rejected.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    exchange_request.status = new_status
    exchange_request.save()

    return Response({
        'message': 'Exchange request status updated successfully.',
        'request_id': exchange_request.id,
        'status': exchange_request.status
    })


# Mark Exchange Request as Completed
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def exchange_request_complete(request, pk):

    exchange_request = get_object_or_404(
        ExchangeRequest,
        pk=pk
    )

    if request.user not in [
        exchange_request.requester,
        exchange_request.product.seller.user
    ]:
        return Response(
            {'error': 'You are not allowed to update this request.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if exchange_request.status != 'accepted':
        return Response(
            {'error': 'Only accepted requests can be completed.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    exchange_request.status = 'completed'
    exchange_request.save()

    return Response({
        'message': 'Exchange completed successfully.',
        'request_id': exchange_request.id,
        'status': exchange_request.status
    })

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def repair_request_list_create(request):

    if request.method == 'GET':
        requests = RepairRequest.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = RepairRequestSerializer(requests, many=True)
        return Response(serializer.data)

    serializer = RepairRequestSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def repair_request_detail(request, pk):
    repair = get_object_or_404(
        RepairRequest,
        pk=pk,
        user=request.user
    )

    serializer = RepairRequestSerializer(repair)
    return Response(serializer.data)


# 3. Update request status
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def repair_request_status_update(request, pk):

    if not (request.user.is_staff or request.user.is_superuser):
        return Response(
            {'error': 'Only staff/admin can update repair status.'},
            status=status.HTTP_403_FORBIDDEN
        )

    repair = get_object_or_404(RepairRequest, pk=pk)

    new_status = request.data.get('status')
    allowed_statuses = [
        choice[0] for choice in RepairRequest.STATUS_CHOICES
    ]

    if new_status not in allowed_statuses:
        return Response(
            {'error': 'Invalid repair status.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    repair.status = new_status
    repair.save()

    serializer = RepairRequestSerializer(repair)
    return Response(serializer.data)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def recycle_request_list_create(request):

    if request.method == 'GET':
        recycle_requests = RecycleRequest.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = RecycleRequestSerializer(
            recycle_requests,
            many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    item_description = request.data.get('item_description', '').strip()

    if not item_description:
        return Response(
            {'error': 'Item description is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    recycle_request = RecycleRequest.objects.create(
        user=request.user,
        item_description=item_description
    )

    serializer = RecycleRequestSerializer(recycle_request)

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED
    )


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def recycle_request_update_status(request, pk):

    recycle_request = get_object_or_404(RecycleRequest, pk=pk)

    new_status = request.data.get('status')

    allowed_statuses = ['Pending', 'Approved', 'Rejected', 'Completed']

    if new_status not in allowed_statuses:
        return Response(
            {
                'error': 'Invalid status.',
                'allowed_statuses': allowed_statuses
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    recycle_request.status = new_status
    recycle_request.save()

    serializer = RecycleRequestSerializer(recycle_request)

    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def pickup_list_create(request):
    if request.method == 'GET':
        pickups = Pickup.objects.filter(user=request.user)
        serializer = PickupSerializer(pickups, many=True)
        return Response(serializer.data)

    serializer = PickupSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def pickup_detail(request, pk):
    try:
        pickup = Pickup.objects.get(pk=pk, user=request.user)
    except Pickup.DoesNotExist:
        return Response(
            {'error': 'Pickup not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = PickupSerializer(pickup)
        return Response(serializer.data)

    if request.method in ['PUT', 'PATCH']:
        serializer = PickupSerializer(
            pickup,
            data=request.data,
            partial=(request.method == 'PATCH')
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    pickup.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def pickup_status_update(request, pk):
    try:
        pickup = Pickup.objects.get(pk=pk, user=request.user)
    except Pickup.DoesNotExist:
        return Response(
            {'error': 'Pickup not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    new_status = request.data.get('status')

    if not new_status:
        return Response(
            {'error': 'Status is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    allowed_statuses = [
        choice[0] for choice in Pickup._meta.get_field('status').choices
    ]

    if new_status not in allowed_statuses:
        return Response(
            {'error': 'Invalid status', 'allowed_statuses': allowed_statuses},
            status=status.HTTP_400_BAD_REQUEST
        )

    pickup.status = new_status
    pickup.save(update_fields=['status'])

    return Response({
        'message': 'Pickup status updated successfully',
        'id': pickup.pk,
        'status': pickup.status
    })

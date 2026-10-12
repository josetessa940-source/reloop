
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterAPI.as_view(), name='register'),
    path('login/', views.LoginAPI.as_view(), name='login'),
    path('logout/', views.LogoutAPI.as_view(), name='logout'),
    path('user-details/', views.UserDetailsAPI.as_view(), name='user-details'),
    path('profile/', views.CreateProfileAPI.as_view(), name='create-profile'),
    path('profile/me/', views.MyProfileAPI.as_view(), name='my-profile'),
    path('categories/', views.CategoryListCreateAPI.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', views.CategoryDetailAPI.as_view(), name='category-detail'),
    path('seller/', views.CreateSellerAPI.as_view()),
    path('seller/me/', views.MySellerProfileAPI.as_view()),
    path('admin/sellers/pending/', views.SellerVerificationAPI.as_view(), name='pending-sellers'),
    path('admin/sellers/<int:pk>/verify/', views.SellerVerificationDetailAPI.as_view(), name='verify-seller'),
    path('products/', views.ProductListCreateAPI.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductDetailAPI.as_view(), name='product-detail'),
    path('wishlist/add/', views.WishlistCreateView.as_view(), name='wishlist-add'),
    path('wishlist/', views.WishlistListView.as_view(), name='wishlist-list'),
    path('wishlist/delete/<int:pk>/', views.WishlistDeleteView.as_view(), name='wishlist-delete'),
    path('reviews/', views.ReviewListCreateAPI.as_view(), name='review-list-create'),
    path('reviews/<int:pk>/', views.ReviewDetailAPI.as_view(), name='review-detail'),
    path('offers/', views.OfferListCreateView.as_view(), name='offer-list-create'),
    path('offers/<int:pk>/accept/', views.OfferAcceptView.as_view(), name='offer-accept'),
    path('offers/<int:pk>/reject/', views.OfferRejectView.as_view(), name='offer-reject'),
    path('orders/', views.order_list_create, name='order-list-create'),
]

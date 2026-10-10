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
]
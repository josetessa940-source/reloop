
from django.urls import path
from .views import CreateProfileAPI, MyProfileAPI

urlpatterns = [
    path('profile/', CreateProfileAPI.as_view(), name='create-profile'),
    path('profile/me/', MyProfileAPI.as_view(), name='my-profile'),
]
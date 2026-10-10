from django.contrib import admin
from .models import *

admin.site.register(CustomUser)
admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Seller)
admin.site.register(Product)

from django.contrib import admin
from .models import CustomUser,EmailVerification,Blog,BlogComment,BlogRating,Payment

admin.site.register(CustomUser)
admin.site.register(EmailVerification)
admin.site.register(Blog)
admin.site.register(BlogComment)
admin.site.register(BlogRating)
admin.site.register(Payment)

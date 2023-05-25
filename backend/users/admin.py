from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscription, User


@admin.register(User)
class AdminUser(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "password",
    )
    list_filter = (
        "username",
        "email",
    )


@admin.register(Subscription)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        "subscriber",
        "author",
    )

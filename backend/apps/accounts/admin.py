from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Horus", {"fields": ("role", "partner_group", "phone")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Horus", {"fields": ("role", "partner_group", "phone")}),
    )
    list_display = [
        "username",
        "email",
        "role",
        "partner_group",
        "is_active",
        "is_staff",
    ]
    list_filter = ["role", "partner_group", "is_active", "is_staff"]
    search_fields = ["username", "email", "first_name", "last_name", "phone"]

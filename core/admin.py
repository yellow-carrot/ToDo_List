from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

# Register your models here.

from core.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name']
    search_fields = ['first_name', 'last_name', 'username']
    readonly_fields = ['last_login', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'is_superuser']


admin.site.unregister(Group)

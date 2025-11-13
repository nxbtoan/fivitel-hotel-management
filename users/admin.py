from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Các trường hiển thị trong danh sách người dùng
    list_display = ('username', 'email', 'full_name', 'role', 'is_staff')
    
    # Cấu hình các trường hiển thị trong form chỉnh sửa chi tiết
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('full_name', 'email', 'date_of_birth', 'nationality', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Custom fields', {'fields': ('role',)}),
    )
    
    # Cấu hình các trường hiển thị trong form tạo mới người dùng
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom fields', {'fields': ('full_name', 'date_of_birth', 'nationality', 'phone_number', 'role')}),
    )

# Đăng ký CustomUser với lớp tùy chỉnh CustomUserAdmin
admin.site.register(CustomUser, CustomUserAdmin)
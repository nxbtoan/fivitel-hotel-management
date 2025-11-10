from django.contrib.auth.models import AbstractUser
from django.db import models
from django_countries.fields import CountryField

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Khách hàng'
        STAFF = 'STAFF', 'Nhân viên'
        ADMIN = 'ADMIN', 'Quản lý'

    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.CUSTOMER
    )

    full_name = models.CharField(max_length=255, blank=True, verbose_name="Họ và Tên")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Ngày sinh")
    nationality = CountryField(blank=True, verbose_name="Quốc tịch")
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại")

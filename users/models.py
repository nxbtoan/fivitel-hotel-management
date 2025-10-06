from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Khách hàng'
        RECEPTIONIST = 'RECEPTIONIST', 'Lễ tân'
        CRM_STAFF = 'CRM_STAFF', 'Nhân viên CSKH'
        ADMIN = 'ADMIN', 'Quản lý'

    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.CUSTOMER
    )
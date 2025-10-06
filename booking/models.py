from django.db import models
from django.conf import settings # Dùng để gọi tới CustomUser

class RoomType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên loại phòng")
    description = models.TextField(verbose_name="Mô tả")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá cơ bản/đêm")
    amenities = models.TextField(verbose_name="Tiện ích", help_text="Mỗi tiện ích cách nhau bởi dấu phẩy")

    def __str__(self):
        return self.name

class Room(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Còn trống'
        BOOKED = 'BOOKED', 'Đã đặt'
        CLEANING = 'CLEANING', 'Đang dọn dẹp'

    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms', verbose_name="Loại phòng")
    room_number = models.CharField(max_length=10, unique=True, verbose_name="Số phòng")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE, verbose_name="Trạng thái")

    def __str__(self):
        return f"{self.room_type.name} - {self.room_number}"

class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Chờ xác nhận'
        CONFIRMED = 'CONFIRMED', 'Đã xác nhận'
        CANCELLED = 'CANCELLED', 'Đã hủy'

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='bookings', verbose_name="Khách hàng")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, related_name='bookings', verbose_name="Phòng")
    check_in_date = models.DateField(verbose_name="Ngày nhận phòng")
    check_out_date = models.DateField(verbose_name="Ngày trả phòng")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tổng giá")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name="Trạng thái đơn")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Đơn #{self.id} - {self.customer.username}"
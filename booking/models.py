from django.db import models
from django.conf import settings
from services.models import Service
from django_countries.fields import CountryField
from django.utils import timezone
from datetime import timedelta

import uuid

class RoomType(models.Model):
    """Danh mục phòng cao nhất (VD: Standard, Deluxe, Suite)."""
    name = models.CharField(max_length=100, verbose_name="Tên loại phòng")
    description = models.TextField(blank=True, verbose_name="Mô tả chung")
    image = models.ImageField(upload_to='room_types/', blank=True, null=True, verbose_name="Ảnh đại diện")

    def __str__(self):
        return self.name

class RoomClass(models.Model):
    """Các hạng phòng cụ thể trong một Loại phòng (VD: Deluxe Hướng Vườn)."""
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='classes', verbose_name="Thuộc loại phòng")
    name = models.CharField(max_length=100, verbose_name="Tên hạng phòng")
    description = models.TextField(verbose_name="Mô tả chi tiết")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá cơ bản/đêm")
    area = models.CharField(max_length=50, verbose_name="Diện tích")
    amenities = models.TextField(verbose_name="Tiện ích", help_text="Mỗi tiện ích cách nhau bởi dấu phẩy")
    image = models.ImageField(upload_to='room_classes/', blank=True, null=True, verbose_name="Ảnh hạng phòng")

    def __str__(self):
        return f"{self.room_type.name} - {self.name}"

class Room(models.Model):
    """Các phòng vật lý, có số phòng cụ thể (VD: D201)."""
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Còn trống'
        OCCUPIED = 'OCCUPIED', 'Đang có khách'
        CLEANING = 'CLEANING', 'Đang dọn dẹp'

    room_class = models.ForeignKey(RoomClass, on_delete=models.CASCADE, related_name='rooms', verbose_name="Thuộc hạng phòng")
    room_number = models.CharField(max_length=10, unique=True, verbose_name="Số phòng")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    def __str__(self):
        return self.room_number

class Booking(models.Model):
    """Lưu thông tin một đơn đặt phòng."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Chờ xác nhận'
        CONFIRMED = 'CONFIRMED', 'Đã xác nhận'
        CHECKED_IN = 'CHECKED_IN', 'Đã nhận phòng'
        COMPLETED = 'COMPLETED', 'Đã hoàn thành'
        CANCELLED = 'CANCELLED', 'Đã hủy'

    class PaymentMethod(models.TextChoices):
        PAY_LATER = 'PAY_LATER', 'Thanh toán khi nhận phòng'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Chuyển khoản ngân hàng'

    booking_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    room_class = models.ForeignKey(RoomClass, on_delete=models.SET_NULL, null=True, verbose_name="Hạng phòng đã chọn")
    assigned_room = models.ForeignKey(
        Room, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='bookings_assigned',
        verbose_name="Phòng đã gán"
    )
    
    guest_full_name = models.CharField(max_length=255, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone_number = models.CharField(max_length=20, blank=True)
    guest_nationality = CountryField(blank=True, verbose_name="Quốc tịch khách vãng lai")

    check_in_date = models.DateField()
    check_out_date = models.DateField()

    room_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Tiền phòng")
    services_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Tiền dịch vụ")

    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    additional_services = models.ManyToManyField(Service, blank=True, verbose_name="Dịch vụ đi kèm")
    special_requests = models.TextField(blank=True, verbose_name="Yêu cầu đặc biệt")
    created_at = models.DateTimeField(auto_now_add=True)

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.PAY_LATER,
        verbose_name="Phương thức thanh toán"
    )

    @property
    def is_cancellable(self):
        """
        Kiểm tra xem đơn hàng có thể hủy được không.
        Trả về True nếu ngày check-in còn xa hơn 24h và trạng thái chưa phải là đã hủy.
        """
        cancellable_deadline = timezone.now().date() + timedelta(days=1)
        return self.check_in_date > cancellable_deadline and self.status != self.Status.CANCELLED
    
    @property
    def is_editable(self):
        """
        Kiểm tra xem đơn hàng có thể chỉnh sửa được không.
        Trả về True nếu ngày check-in vẫn còn ở tương lai và trạng thái hợp lệ.
        """
        return self.check_in_date > timezone.now().date() and self.status in [self.Status.PENDING, self.Status.CONFIRMED]

class PaymentProof(models.Model):
    """
    Lưu trữ ảnh bằng chứng thanh toán cho một đơn đặt phòng.
    """
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment_proof')
    image = models.ImageField(upload_to='payment_proofs/', verbose_name="Ảnh bằng chứng")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bằng chứng cho Đơn hàng #{self.booking.id}"
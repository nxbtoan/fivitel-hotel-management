from django.db import models
from django.conf import settings
from services.models import Service
from django_countries.fields import CountryField
from django.utils import timezone
from datetime import timedelta

import uuid
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class RoomType(models.Model):
    """Danh mục phòng cao nhất (VD: Standard, Deluxe, Suite)."""
    name = models.CharField(max_length=100, verbose_name="Tên loại phòng")
    description = models.TextField(blank=True, verbose_name="Mô tả chung")
    image = models.ImageField(upload_to='media/room_types/', blank=True, null=True, verbose_name="Ảnh đại diện")

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
    image = models.ImageField(upload_to='media/room_classes/', blank=True, null=True, verbose_name="Ảnh hạng phòng")

    def __str__(self):
        return f"{self.room_type.name} - {self.name}"

class Room(models.Model):
    """Các phòng vật lý, có số phòng cụ thể (VD: D201)."""
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Còn trống'
        OCCUPIED = 'OCCUPIED', 'Đang có khách'
        CLEANING = 'CLEANING', 'Đang dọn dẹp'
        MAINTENANCE = 'MAINTENANCE', 'Đang bảo trì'

    room_class = models.ForeignKey(RoomClass, on_delete=models.CASCADE, related_name='rooms', verbose_name="Thuộc hạng phòng")
    room_number = models.CharField(max_length=10, unique=True, verbose_name="Số phòng")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE, verbose_name="Trạng thái phòng")

    def __str__(self):
        return self.room_number

class Booking(models.Model):
    """Lưu thông tin một đơn đặt phòng."""
    class Status(models.TextChoices):
        # Đơn đặt sớm, khách có thể sửa
        PENDING_REVIEW = 'PENDING_REVIEW', 'Đang xem xét'
        # Đơn đặt gấp, khóa, bắt buộc thanh toán
        PENDING_PAYMENT = 'PENDING_PAYMENT', 'Chờ thanh toán'
        # Đơn đặt sớm đã bị khóa, chờ thanh toán
        READY_FOR_PAYMENT = 'READY_FOR_PAYMENT', 'Sẵn sàng thanh toán'
        # Khách đã upload chứng từ
        PAYMENT_PENDING_VERIFICATION = 'PAYMENT_PENDING_VERIFICATION', 'Chờ xác nhận TT'
        # Kế toán đã xác nhận thanh toán
        PAID = 'PAID', 'Đã thanh toán'
        # Lễ tân đã gán phòng
        CONFIRMED = 'CONFIRMED', 'Đã xác nhận' 
        CHECKED_IN = 'CHECKED_IN', 'Đã nhận phòng'
        COMPLETED = 'COMPLETED', 'Đã hoàn thành'
        # Đơn đặt gấp quá 2h chưa trả tiền
        EXPIRED = 'EXPIRED', 'Đã hết hạn'
        CANCELLED = 'CANCELLED', 'Đã hủy'

    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'BANK_TRANSFER', 'Chuyển khoản ngân hàng'

    booking_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    room_class = models.ForeignKey(RoomClass, on_delete=models.SET_NULL, null=True, verbose_name="Hạng phòng đã chọn")
    assigned_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings_assigned',verbose_name="Phòng đã gán")
    
    guest_full_name = models.CharField(max_length=255, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone_number = models.CharField(max_length=20, blank=True)
    guest_nationality = CountryField(blank=True, verbose_name="Quốc tịch khách vãng lai")

    check_in_date = models.DateField()
    check_out_date = models.DateField()

    adults = models.PositiveIntegerField(default=1, verbose_name="Số người lớn")
    children = models.PositiveIntegerField(default=0, verbose_name="Số trẻ em")

    room_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Tiền phòng")
    services_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Tiền dịch vụ")

    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING_REVIEW)
    additional_services = models.ManyToManyField(Service, blank=True, verbose_name="Dịch vụ đi kèm")
    special_requests = models.TextField(blank=True, verbose_name="Yêu cầu đặc biệt")
    created_at = models.DateTimeField(auto_now_add=True)

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.BANK_TRANSFER,
        verbose_name="Phương thức thanh toán"
    )

    is_locked = models.BooleanField(
        default=False, 
        verbose_name="Đã khóa (không thể sửa)"
    )
    payment_date = models.DateTimeField(
        null=True, blank=True, 
        verbose_name="Thời điểm tải chứng từ"
    )

    @property
    def is_cancellable(self):
        """
        Chỉ có thể hủy khi đơn chưa bị khóa và chưa bị hủy
        """
        return self.status == self.Status.PENDING_REVIEW and (not self.is_locked)
    
    @property
    def is_editable(self):
        """
        Chỉ có thể sửa khi đơn chưa bị khóa
        """
        return (self.status == self.Status.PENDING_REVIEW) and (not self.is_locked)
    
    @property
    def is_payment_ready(self):
        """
        Kiểm tra xem đơn hàng đã sẵn sàng để thanh toán chưa.
        Hoặc là đơn đặt gấp, hoặc là đơn đã bị khóa
        """
        return self.status in [
            self.Status.PENDING_REVIEW, 
            self.Status.PENDING_PAYMENT, 
            self.Status.READY_FOR_PAYMENT
        ]

    def send_booking_email(self, subject, template_name):
        """
        Hàm helper để gửi email thông báo/hóa đơn cho khách hàng.
        """
        recipient_email = self.guest_email
        if not recipient_email and self.customer:
            recipient_email = self.customer.email

        if not recipient_email:
            print(f"Không thể gửi mail cho đơn #{self.id} vì không có email.")
            return

        context = {'booking': self}
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL # Lấy từ settings.py

        try:
            send_mail(
                subject,
                plain_message,
                from_email,
                [recipient_email],
                html_message=html_message
            )
        except Exception as e:
            # Ghi lại lỗi nếu có (quan trọng cho gỡ lỗi)
            print(f"LỖI GỬI MAIL cho đơn #{self.id}: {e}")

class PaymentProof(models.Model):
    """
    Lưu trữ ảnh bằng chứng thanh toán cho một đơn đặt phòng.
    """
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment_proof')
    image = models.ImageField(upload_to='media/payment_proofs/', verbose_name="Ảnh bằng chứng")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bằng chứng cho Đơn hàng #{self.booking.id}"
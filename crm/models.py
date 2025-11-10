import uuid
from django.db import models
from django.conf import settings
from users.models import CustomUser

class Ticket(models.Model):
    """
    Lưu trữ thông tin về một yêu cầu hỗ trợ hoặc khiếu nại của khách hàng.
    """
    class Type(models.TextChoices):
        CONSULTATION = 'CONSULTATION', 'Tư vấn Dịch vụ'
        BOOKING_SUPPORT = 'BOOKING_SUPPORT', 'Hỗ trợ Đặt phòng'
        COMPLAINT = 'COMPLAINT', 'Khiếu nại'
        OTHER = 'OTHER', 'Yêu cầu Khác'

    class ComplaintType(models.TextChoices):
        ROOM_QUALITY = 'ROOM_QUALITY', 'Về chất lượng phòng'
        STAFF_ATTITUDE = 'STAFF_ATTITUDE', 'Về thái độ nhân viên'
        SERVICE_ISSUES = 'SERVICE_ISSUES', 'Về chất lượng dịch vụ'
        BILLING_ERROR = 'BILLING_ERROR', 'Về sai sót thanh toán'
        OTHER = 'OTHER', 'Vấn đề khác'

    class Status(models.TextChoices):
        NEW = 'NEW', 'Mới'
        IN_PROGRESS = 'IN_PROGRESS', 'Đang xử lý'
        AWAITING_STAFF_RESPONSE = 'AWAITING_STAFF', 'Chờ Nhân viên Phản hồi'
        RESOLVED = 'RESOLVED', 'Đã hoàn thành'

    ticket_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Mã yêu cầu")
    customer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets', verbose_name="Khách hàng (nếu có)")
    guest_full_name = models.CharField(max_length=100, blank=True, verbose_name="Họ tên khách vãng lai")
    guest_email = models.EmailField(blank=True, verbose_name="Email khách vãng lai")
    guest_phone_number = models.CharField(max_length=20, blank=True, verbose_name="SĐT khách vãng lai")
    subject = models.CharField(max_length=255, verbose_name="Tiêu đề", blank=True)
    incident_time = models.DateTimeField(verbose_name="Thời gian xảy ra vụ việc", null=True, blank=True)
    attachment = models.FileField(upload_to='media/ticket_attachments/', verbose_name="Tệp đính kèm", null=True, blank=True)
    complaint_type = models.CharField(max_length=20, choices=ComplaintType.choices, verbose_name="Loại khiếu nại", blank=True, null=True)
    type = models.CharField(max_length=20, choices=Type.choices, verbose_name="Loại yêu cầu")
    description = models.TextField(verbose_name="Nội dung chi tiết")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, verbose_name="Trạng thái")
    resolution_details = models.TextField(
        verbose_name="Kết quả xử lý (cuối cùng)", 
        blank=True, null=True,
        help_text="Ghi lại nguyên nhân, giải pháp, đền bù (nếu có) sau khi ticket đã hoàn thành."
    )
    assigned_to = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='assigned_tickets', 
        verbose_name="Nhân viên xử lý",
        limit_choices_to={'is_staff': True} 
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject or f"Yêu cầu từ {self.customer or self.guest_full_name}"

class TicketResponse(models.Model):
    """
    Lưu trữ nội dung của mỗi lần trao đổi trong một Ticket.
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='responses', verbose_name="Yêu cầu")
    responder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Người phản hồi")
    message = models.TextField(verbose_name="Nội dung phản hồi")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Phản hồi từ {self.responder.username} cho {self.ticket.ticket_id}"
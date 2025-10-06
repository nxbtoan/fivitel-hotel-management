import uuid
from django.db import models
from django.conf import settings

class Ticket(models.Model):
    class Type(models.TextChoices):
        INQUIRY = 'INQUIRY', 'Tư vấn'
        COMPLAINT = 'COMPLAINT', 'Khiếu nại'
        SUPPORT = 'SUPPORT', 'Hỗ trợ sau lưu trú'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Mới'
        IN_PROGRESS = 'IN_PROGRESS', 'Đang xử lý'
        RESOLVED = 'RESOLVED', 'Đã hoàn thành'

    ticket_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Mã yêu cầu")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets', verbose_name="Khách hàng")
    type = models.CharField(max_length=20, choices=Type.choices, verbose_name="Loại yêu cầu")
    title = models.CharField(max_length=255, verbose_name="Tiêu đề")
    description = models.TextField(verbose_name="Nội dung chi tiết")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, verbose_name="Trạng thái")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', verbose_name="Nhân viên xử lý")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_type_display()}] {self.title}"

class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments', verbose_name="Yêu cầu")
    file = models.FileField(upload_to='ticket_attachments/', verbose_name="Tệp đính kèm")

    def __str__(self):
        return f"Tệp đính kèm cho {self.ticket.ticket_id}"

class TicketResponse(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='responses', verbose_name="Yêu cầu")
    responder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Người phản hồi")
    message = models.TextField(verbose_name="Nội dung phản hồi")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Phản hồi từ {self.responder.username} cho {self.ticket.ticket_id}"
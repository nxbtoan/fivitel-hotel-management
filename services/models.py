from django.db import models
from django.urls import reverse

class ServiceCategory(models.Model):
    """Lưu các loại dịch vụ (VD: Ăn uống, Thư giãn...)."""
    name = models.CharField(max_length=100, verbose_name="Tên loại dịch vụ")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    image = models.ImageField(
        upload_to='media/service_categories/', 
        null=True,
        blank=True,
        verbose_name="Ảnh minh họa"
    )

    def __str__(self):
        return self.name

class Service(models.Model):
    """Lưu các dịch vụ đi kèm cụ thể (VD: Đưa đón sân bay, Tour tham quan...)."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Đang hoạt động'
        INACTIVE = 'INACTIVE', 'Không hoạt động'
        MAINTENANCE = 'MAINTENANCE', 'Đang bảo trì'

    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services', verbose_name="Loại dịch vụ")
    name = models.CharField(max_length=200, verbose_name="Tên dịch vụ")
    description = models.TextField(blank=True, verbose_name="Mô tả chung")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá", default=0.00)
    price_unit = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Đơn vị tính giá", 
        help_text="Ví dụ: 'mỗi khách', 'mỗi giờ', 'trọn gói'"
    )
    image = models.ImageField(
        upload_to='media/services/',
        null=True,
        blank=True,
        verbose_name="Ảnh minh họa"
    )
    highlights = models.TextField(
        blank=True, 
        verbose_name="Điểm nổi bật", 
        help_text="Mỗi điểm nổi bật trên một dòng (sẽ hiển thị dạng bullet point)."
    )
    terms_conditions = models.TextField(
        blank=True, 
        verbose_name="Điều khoản & Điều kiện",
        help_text="Mỗi điều khoản trên một dòng."
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Trạng thái dịch vụ"
    )

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        """Tạo URL chuẩn cho trang chi tiết."""
        return reverse('service_detail', kwargs={'pk': self.pk})
    
    def get_highlights_list(self):
        """Hàm helper để tách các dòng highlights ra thành danh sách."""
        return [line.strip() for line in self.highlights.splitlines() if line.strip()]
    
    def get_terms_list(self):
        """Hàm helper để tách các dòng điều khoản ra thành danh sách."""
        return [line.strip() for line in self.terms_conditions.splitlines() if line.strip()]

class ServiceImage(models.Model):
    """Lưu các ảnh trong thư viện (gallery) của một dịch vụ."""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='gallery_images', verbose_name="Dịch vụ")
    image = models.ImageField(upload_to='media/services/gallery/', verbose_name="Ảnh")
    alt_text = models.CharField(max_length=255, blank=True, verbose_name="Văn bản thay thế")

    def __str__(self):
        return f"Ảnh cho {self.service.name}"
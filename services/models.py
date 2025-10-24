from django.db import models

class ServiceCategory(models.Model):
    """Lưu các loại dịch vụ (VD: Ăn uống, Thư giãn...)."""
    name = models.CharField(max_length=100, verbose_name="Tên loại dịch vụ")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    image = models.ImageField(
        upload_to='service_categories/', 
        null=True,
        blank=True,
        verbose_name="Ảnh minh họa"
    )

    def __str__(self):
        return self.name

class Service(models.Model):
    """Lưu các dịch vụ đi kèm cụ thể (VD: Đưa đón sân bay, Tour tham quan...)."""
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services', verbose_name="Loại dịch vụ")
    name = models.CharField(max_length=200, verbose_name="Tên dịch vụ")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá")
    image = models.ImageField(
        upload_to='services/', # Lưu ảnh vào thư mục media/services/
        null=True,
        blank=True,
        verbose_name="Ảnh minh họa"
    )

    def __str__(self):
        return self.name
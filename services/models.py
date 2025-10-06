from django.db import models

class Service(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tên dịch vụ")
    description = models.TextField(verbose_name="Mô tả")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá dịch vụ")
    image = models.ImageField(upload_to='service_images/', null=True, blank=True, verbose_name="Hình ảnh")

    def __str__(self):
        return self.name
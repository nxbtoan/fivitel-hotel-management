from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import RoomType, RoomClass, Room, Booking, PaymentProof

class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_class', 'status')

    list_filter = ('status', 'room_class__room_type', 'room_class')

    search_fields = ('room_number',)

class BookingAdmin(admin.ModelAdmin):
    # Các cột sẽ hiển thị trong danh sách đơn hàng
    list_display = (
        'id', 
        'customer_info', 
        'room_class', 
        'check_in_date', 
        'status', 
        'payment_method', 
        'view_payment_proof' # Cột hiển thị ảnh bằng chứng
    )
    
    # Bộ lọc ở sidebar bên phải
    list_filter = ('status', 'payment_method', 'check_in_date')
    
    # Các trường có thể tìm kiếm
    search_fields = ('id', 'customer__username', 'guest_full_name')
    
    # Cho phép chỉnh sửa trạng thái trực tiếp từ danh sách
    list_editable = ('status',)

    def customer_info(self, obj):
        """Hàm tùy chỉnh để hiển thị thông tin khách hàng cho gọn."""
        if obj.customer:
            return obj.customer.username
        return obj.guest_full_name
    customer_info.short_description = 'Khách hàng' # Đặt tên cho cột

    def view_payment_proof(self, obj):
        """
        Hàm tùy chỉnh để hiển thị ảnh bằng chứng thanh toán.
        Tạo một ảnh thumbnail có thể click để xem ảnh gốc.
        """
        if hasattr(obj, 'payment_proof') and obj.payment_proof.image:
            image_url = obj.payment_proof.image.url
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" width="100" /></a>', 
                image_url
            )
        return "Chưa có"
    view_payment_proof.short_description = 'Bằng chứng TT' # Đặt tên cho cột

admin.site.register(RoomType)
admin.site.register(RoomClass)
admin.site.register(Room, RoomAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(PaymentProof) 
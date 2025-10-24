from django.contrib import admin
from django.utils.html import format_html
from .models import RoomType, RoomClass, Room, Booking, PaymentProof

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    """Giao diện quản trị cho Loại phòng."""
    list_display = ('name', 'description', 'image')
    search_fields = ('name',)

@admin.register(RoomClass)
class RoomClassAdmin(admin.ModelAdmin):
    """Giao diện quản trị cho Hạng phòng."""
    list_display = ('name', 'room_type', 'base_price', 'area', 'get_amenities_preview')
    list_filter = ('room_type',)
    search_fields = ('name', 'room_type__name')

    def get_amenities_preview(self, obj):
        """Hiển thị một đoạn xem trước ngắn của các tiện ích."""
        amenities = [amenity.strip() for amenity in obj.amenities.split(',')]
        # Chỉ hiển thị 3 tiện ích đầu tiên
        return ", ".join(amenities[:3]) + ('...' if len(amenities) > 3 else '')
    get_amenities_preview.short_description = 'Tiện ích (Xem trước)'

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Giao diện quản trị cho từng Phòng cụ thể."""
    list_display = ('room_number', 'room_class', 'status')
    list_filter = ('status', 'room_class__room_type', 'room_class')
    list_editable = ('status',) # Cho phép sửa trạng thái trực tiếp từ danh sách
    search_fields = ('room_number',)
    list_per_page = 20 # Thêm phân trang

class PaymentProofInline(admin.StackedInline):
    """
    Giao diện inline cho Bằng chứng Thanh toán.
    Cho phép xem và thêm bằng chứng thanh toán ngay bên trong trang chi tiết của Booking.
    """
    model = PaymentProof
    can_delete = False
    verbose_name_plural = 'Bằng chứng Thanh toán'
    readonly_fields = ('image_preview',) # Hiển thị ảnh xem trước không cho phép sửa

    def image_preview(self, obj):
        """Tạo một ảnh thumbnail có thể click được của bằng chứng thanh toán."""
        if obj.image:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="200"/></a>', obj.image.url)
        return "Không có ảnh"
    image_preview.short_description = 'Xem trước ảnh'

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Giao diện quản trị toàn diện cho các Đơn đặt phòng."""
    list_display = (
        'id',
        'customer_info',
        'room_class',
        'check_in_date',
        'status',
        'payment_method',
        'total_price'
    )
    list_filter = ('status', 'payment_method', 'check_in_date', 'room_class')
    list_editable = ('status',)
    search_fields = ('id', 'customer__username', 'guest_full_name', 'assigned_room__room_number')
    date_hierarchy = 'check_in_date' # Thêm thanh điều hướng theo ngày ở trên cùng
    ordering = ('-check_in_date',)
    list_per_page = 20

    # Trang chi tiết sẽ được sắp xếp thành các mục
    fieldsets = (
        ('Thông tin Đơn hàng', {
            'fields': ('id', 'status', 'room_class', 'assigned_room')
        }),
        ('Lịch trình & Chi phí', {
            'fields': ('check_in_date', 'check_out_date', 'total_price', 'payment_method')
        }),
        ('Thông tin Khách hàng', {
            'fields': ('customer', ('guest_full_name', 'guest_email', 'guest_phone_number'))
        }),
        ('Dịch vụ & Yêu cầu', {
            'fields': ('additional_services', 'special_requests')
        }),
    )

    readonly_fields = ('id',) # Không cho phép thay đổi ID của đơn hàng
    inlines = [PaymentProofInline] # Nhúng form PaymentProof vào bên trong trang Booking

    def customer_info(self, obj):
        """Hàm tùy chỉnh để hiển thị thông tin khách hàng một cách ngắn gọn."""
        if obj.customer:
            return obj.customer.get_full_name() or obj.customer.username
        return f"{obj.guest_full_name} (Khách vãng lai)"
    customer_info.short_description = 'Khách hàng'
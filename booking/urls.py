from django.urls import path
from . import views

urlpatterns = [
    # URL cho Trang 1: Hiển thị danh sách các Loại phòng
    path('', views.room_type_list_view, name='room_type_list'),
    
    # URL cho Trang 2: Hiển thị các Hạng phòng
    path('<int:room_type_id>/', views.room_class_list_view, name='room_class_list'),

    # URL cho Trang 3: Chọn tùy chọn đặt phòng
    path('options/<int:room_class_id>/', views.booking_options_view, name='booking_options'),

    # URL cho Trang 4: Nhập thông tin khách hàng và thanh toán
    path('checkout/', views.checkout_view, name='checkout'),

    # URL cho Trang 4b: Hướng dẫn thanh toán (nếu chọn chuyển khoản)
    path('payment/<int:booking_pk>/', views.payment_guidance_view, name='payment_guidance'),

    # URL cho Trang 5: Xác nhận đặt phòng thành công
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
]
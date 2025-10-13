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

    # URL cho Trang 5: Xem và quản lý các đặt phòng của khách hàng
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),

    # URL cho Trang 6: Chi tiết đặt phòng
    path('my-bookings/<int:pk>/', views.booking_detail_view, name='booking_detail'),

    # URL cho Hủy đặt phòng
    path('my-bookings/<int:pk>/cancel/', views.cancel_booking_view, name='cancel_booking'),


    # URL để nhân viên xem và quản lý tất cả các đặt phòng
    path('dashboard/bookings/', views.manage_bookings_view, name='manage_bookings'),

    # URL để nhân viên xác nhận đặt phòng cho khách
    path('dashboard/bookings/<int:pk>/confirm/', views.confirm_booking_view, name='confirm_booking'),

    # URL để nhân viên hủy đặt phòng cho khách
    path('dashboard/bookings/<int:pk>/cancel/', views.cancel_booking_by_staff_view, name='cancel_booking_by_staff'),

    # URL để nhân viên cập nhật trạng thái phòng
    path('dashboard/rooms/', views.manage_rooms_view, name='manage_rooms'),

    # URL để nhân viên gán phòng cụ thể cho đặt phòng
    path('dashboard/bookings/<int:pk>/check-in/', views.check_in_view, name='check_in'),

    # URL để nhân viên xử lý check-out cho đặt phòng
    path('dashboard/bookings/<int:pk>/check-out/', views.check_out_view, name='check_out'),

]
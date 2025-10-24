from django.urls import path
from . import views

# app_name = 'booking_dashboard' # Tùy chọn: Thêm namespace nếu cần

urlpatterns = [
    # URL để nhân viên xem và quản lý tất cả các đặt phòng
    path('bookings/', views.manage_bookings_view, name='manage_bookings'),
    path('bookings/<int:pk>/', views.staff_booking_detail_view, name='staff_booking_detail'),
    path('bookings/<int:pk>/confirm/', views.confirm_booking_view, name='confirm_booking'),
    path('bookings/<int:pk>/cancel/', views.cancel_booking_by_staff_view, name='cancel_booking_by_staff'),
    path('bookings/<int:pk>/check-in/', views.check_in_view, name='check_in'),
    path('bookings/<int:pk>/check-out/', views.check_out_view, name='check_out'),

    # URL để nhân viên cập nhật trạng thái phòng
    path('rooms/', views.manage_rooms_view, name='manage_rooms'),

    # URLs CHO QUẢN LÝ LOẠI PHÒNG
    path('room-types/', views.RoomTypeListView.as_view(), name='room_type_list'),
    path('room-types/new/', views.RoomTypeCreateView.as_view(), name='room_type_create'),
    path('room-types/<int:pk>/edit/', views.RoomTypeUpdateView.as_view(), name='room_type_update'),
    path('room-types/<int:pk>/delete/', views.RoomTypeDeleteView.as_view(), name='room_type_delete'),

    # URLs CHO QUẢN LÝ HẠNG PHÒNG
    path('room-classes/', views.RoomClassListView.as_view(), name='room_class_list_admin'),
    path('room-classes/new/', views.RoomClassCreateView.as_view(), name='room_class_create'),
    path('room-classes/<int:pk>/edit/', views.RoomClassUpdateView.as_view(), name='room_class_update'),
    path('room-classes/<int:pk>/delete/', views.RoomClassDeleteView.as_view(), name='room_class_delete'),

    # URLs CHO QUẢN LÝ PHÒNG
    path('rooms-management/', views.RoomListView.as_view(), name='room_list_admin'),
    path('rooms-management/new/', views.RoomCreateView.as_view(), name='room_create'),
    path('rooms-management/<int:pk>/edit/', views.RoomUpdateView.as_view(), name='room_update'),
    path('rooms-management/<int:pk>/delete/', views.RoomDeleteView.as_view(), name='room_delete'),
]
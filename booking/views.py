from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required,  user_passes_test
from django.contrib import messages

from .models import RoomType, RoomClass, Room, Service, PaymentProof, Booking
from .forms import BookingOptionsForm, CheckoutForm, PaymentProofForm
from datetime import timedelta, datetime

def room_type_list_view(request):
    """
    Hiển thị danh sách các LOẠI PHÒNG (RoomType) có trong khách sạn.
    Đây là trang bắt đầu của luồng đặt phòng.
    """
    room_types = RoomType.objects.all()
    context = {
        'room_types': room_types
    }
    return render(request, 'booking/room_type_list.html', context)

def room_class_list_view(request, room_type_id):
    """
    Hiển thị danh sách các HẠNG PHÒNG và số lượng phòng còn trống.
    Vô hiệu hóa nút đặt phòng nếu hạng phòng đã hết.
    """
    room_type = get_object_or_404(RoomType, pk=room_type_id)
    # Sử dụng annotate để tạo một trường mới 'available_rooms_count'
    # đếm số phòng ('rooms') có trạng thái là 'AVAILABLE'
    room_classes = room_type.classes.annotate(
        available_rooms_count=Count('rooms', filter=Q(rooms__status='AVAILABLE'))
    ).all()

    # Xử lý chuỗi tiện ích để hiển thị
    for r_class in room_classes:
        r_class.amenities_list = [amenity.strip() for amenity in r_class.amenities.split(',')]

    context = {
        'room_type': room_type,
        'room_classes': room_classes,
    }
    return render(request, 'booking/room_class_list.html', context)

def booking_options_view(request, room_class_id):
    """
    Xử lý Bước 1: Trang Tùy chọn Đặt phòng.
    - Hiển thị form chọn Ngày, Số khách, Dịch vụ.
    - Hiển thị các lựa chọn Nâng hạng phòng.
    - Khi submit, lưu lựa chọn vào session và chuyển sang trang Checkout.
    """
    room_class = get_object_or_404(RoomClass, pk=room_class_id)
    
    # Lấy các hạng phòng khác cùng loại phòng và có giá cao hơn để gợi ý nâng hạng
    upgrade_options = RoomClass.objects.filter(
        room_type=room_class.room_type, 
        base_price__gt=room_class.base_price
    ).order_by('base_price')

    if request.method == 'POST':
        form = BookingOptionsForm(request.POST)
        if form.is_valid():
            options = form.cleaned_data
            # Lưu các lựa chọn vào session
            request.session['booking_options'] = {
                'room_class_id': room_class.id,
                'check_in': options['check_in_date'].isoformat(),
                'check_out': options['check_out_date'].isoformat(),
                'adults': options['adults'],
                'children': options['children'],
                'service_ids': [service.id for service in options['additional_services']],
            }
            return redirect('checkout') # Chuyển đến trang checkout
    else:
        form = BookingOptionsForm()

    context = {
        'form': form,
        'room_class': room_class,
        'upgrade_options': upgrade_options
    }

    return render(request, 'booking/booking_options.html', context)

def checkout_view(request):
    """
    Xử lý Bước 2 (Trang Checkout): Điền thông tin khách hàng và hoàn tất đặt phòng.

    - Đọc dữ liệu từ session (lựa chọn ở bước trước).
    - Hiển thị form điền thông tin cá nhân.
    - Khi người dùng nhấn "Đặt phòng" (POST), tạo bản ghi Booking và chuyển hướng.
    """
    
    # --- PHẦN 1: LẤY DỮ LIỆU TỪ SESSION VÀ TÍNH TOÁN ---
    booking_options = request.session.get('booking_options')
    if not booking_options:
        return redirect('homepage') # Bảo vệ, nếu không có session thì về trang chủ

    room_class = get_object_or_404(RoomClass, pk=booking_options['room_class_id'])
    selected_services = Service.objects.filter(id__in=booking_options.get('service_ids', []))
    
    check_in = datetime.fromisoformat(booking_options['check_in']).date()
    check_out = datetime.fromisoformat(booking_options['check_out']).date()
    
    duration = (check_out - check_in).days
    room_price = room_class.base_price * duration
    services_price = sum(service.price for service in selected_services)
    total_price = room_price + services_price

    # --- PHẦN 2: XỬ LÝ KHI NGƯỜI DÙNG NHẤN NÚT "ĐẶT PHÒNG" ---
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            guest_data = form.cleaned_data
            
            available_room = Room.objects.filter(room_class=room_class, status='AVAILABLE').first()
            if not available_room:
                # Đây là lúc trang error_page.html sẽ được dùng
                return render(request, 'booking/error_page.html', {'message': 'Rất tiếc, hạng phòng này vừa hết phòng trống.'})

            # Chuẩn bị dữ liệu để tạo Booking
            booking_details = {
                'room_class': room_class,
                'check_in_date': check_in,
                'check_out_date': check_out,
                'total_price': total_price,
                'payment_method': guest_data['payment_method'],
            }

            # Gán thông tin khách hàng
            if request.user.is_authenticated and guest_data['booking_for'] == 'myself':
                booking_details['customer'] = request.user
            else:
                booking_details.update({
                    'guest_full_name': guest_data['full_name'],
                    'guest_email': guest_data['email'],
                    'guest_phone_number': guest_data['phone_number'],
                    'guest_nationality': guest_data['nationality'],
                })

            # Tạo bản ghi Booking mới trong database
            new_booking = Booking.objects.create(**booking_details)
            
            # Gán các dịch vụ đi kèm vào đơn hàng
            if selected_services:
                new_booking.additional_services.set(selected_services)
            
            # Dọn dẹp session
            del request.session['booking_options']
            request.session['last_booking_id'] = new_booking.pk
            
            # --- ĐIỂM RẼ NHÁNH QUAN TRỌNG ---
            if new_booking.payment_method == 'BANK_TRANSFER':
                # Nếu chọn Chuyển khoản, đến trang hướng dẫn thanh toán
                return redirect('payment_guidance', booking_pk=new_booking.pk)
            else: # Nếu là PAY_LATER (Trả sau)
                # Chuyển thẳng đến trang quản lý các đơn đặt phòng
                return redirect('my_bookings')

    # --- PHẦN 3: XỬ LÝ KHI NGƯỜI DÙNG MỚI VÀO TRANG (GET) ---
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'full_name': request.user.full_name,
                'email': request.user.email,
                'phone_number': request.user.phone_number,
                'nationality': request.user.nationality,
            }
        form = CheckoutForm(initial=initial_data)

    # --- PHẦN 4: GỬI DỮ LIỆU RA TEMPLATE ---
    context = {
        'form': form,
        'room_class': room_class,
        'options': booking_options,
        'duration': duration,
        'room_price': room_price,
        'selected_services': selected_services,
        'services_price': services_price,
        'total_price': total_price,
    }
    return render(request, 'booking/checkout.html', context)

@login_required
def payment_guidance_view(request, booking_pk):
    """
    Hiển thị trang Hướng dẫn thanh toán và xử lý việc tải lên bằng chứng.
    """
    booking = get_object_or_404(Booking, pk=booking_pk, customer=request.user)
    
    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.booking = booking
            proof.save()
            return redirect('my_bookings') # Chuyển đến trang quản lý sau khi tải lên
    else:
        form = PaymentProofForm()

    context = {
        'booking': booking,
        'form': form
    }
    return render(request, 'booking/payment_guidance.html', context)

@login_required
def my_bookings_view(request):
    """
    Hiển thị trang "Quản lý Đơn đặt phòng của tôi".
    """
    bookings = Booking.objects.filter(customer=request.user).order_by('-created_at')
    context = {
        'bookings': bookings
    }
    return render(request, 'booking/my_bookings.html', context)

@login_required
def booking_detail_view(request, pk):
    """
    Hiển thị thông tin chi tiết của một đơn đặt phòng cụ thể.
    Đảm bảo chỉ chủ sở hữu của đơn hàng mới có thể xem.
    """
    # Lấy booking, nếu không tìm thấy hoặc không thuộc về user hiện tại, báo lỗi 404
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)
    
    context = {
        'booking': booking
    }
    return render(request, 'booking/booking_detail.html', context)

@login_required
def cancel_booking_view(request, pk):
    """
    Xử lý yêu cầu hủy đơn đặt phòng của khách hàng.
    Chỉ cho phép hủy nếu ngày check-in còn xa hơn 24 giờ.
    """
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)
    
    # Quy tắc: Ngày check-in phải lớn hơn ngày hiện tại + 1 ngày (24h)
    cancellable_deadline = timezone.now().date() + timedelta(days=1)
    
    if request.method == 'POST' and booking.check_in_date > cancellable_deadline and booking.status != 'CANCELLED':
        booking.status = Booking.Status.CANCELLED
        booking.save()
        # (Tùy chọn) Thêm message thông báo thành công
    
    return redirect('my_bookings')

# Hàm kiểm tra xem user có phải là nhân viên không (Lễ tân hoặc Admin)
def is_reception_staff(user):
    return user.is_authenticated and (user.role in ['RECEPTIONIST', 'ADMIN'])

@user_passes_test(is_reception_staff)
def manage_bookings_view(request):
    """
    Hiển thị trang quản lý tất cả đơn đặt phòng cho Lễ tân.
    Cho phép lọc đơn hàng theo trạng thái.
    """
    # Lấy tham số 'status' từ URL, ví dụ: /dashboard/bookings/?status=PENDING
    status_filter = request.GET.get('status')
    
    # Bắt đầu với việc lấy tất cả đơn hàng, sắp xếp mới nhất lên đầu
    # Dùng select_related và prefetch_related để tối ưu truy vấn database
    bookings = Booking.objects.select_related(
        'room_class', 'customer'
    ).prefetch_related(
        'payment_proof'
    ).order_by('-created_at')

    # Nếu có bộ lọc, áp dụng nó
    if status_filter in ['PENDING', 'CONFIRMED', 'CANCELLED']:
        bookings = bookings.filter(status=status_filter)

    context = {
        'bookings': bookings,
        'current_filter': status_filter # Gửi bộ lọc hiện tại sang template để active nút
    }
    return render(request, 'booking/dashboard_bookings.html', context)

@user_passes_test(is_reception_staff)
def confirm_booking_view(request, pk):
    """Xử lý hành động 'Xác nhận' đơn hàng."""
    if request.method == 'POST':
        booking = get_object_or_404(Booking, pk=pk)
        booking.status = Booking.Status.CONFIRMED
        booking.save()
        messages.success(request, f"Đã xác nhận thành công đơn hàng #{booking.id}.")
    return redirect('manage_bookings')

@user_passes_test(is_reception_staff)
def cancel_booking_by_staff_view(request, pk):
    """Xử lý hành động 'Hủy' đơn hàng từ phía nhân viên."""
    if request.method == 'POST':
        booking = get_object_or_404(Booking, pk=pk)
        booking.status = Booking.Status.CANCELLED
        booking.save()
        messages.success(request, f"Đã hủy thành công đơn hàng #{booking.id}.")
    return redirect('manage_bookings')

@user_passes_test(is_reception_staff)
def manage_rooms_view(request):
    """
    Hiển thị trang quản lý trạng thái của tất cả các phòng.
    Cho phép Lễ tân cập nhật trạng thái (Còn trống, Đang dọn dẹp, Đã có khách).
    """
    # Xử lý yêu cầu cập nhật trạng thái khi Lễ tân gửi form
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        new_status = request.POST.get('status')
        
        # Tìm phòng và cập nhật trạng thái
        room_to_update = get_object_or_404(Room, pk=room_id)
        if new_status in Room.Status.values:
            room_to_update.status = new_status
            room_to_update.save()
            messages.success(request, f"Đã cập nhật trạng thái cho phòng {room_to_update.room_number}.")
        
        # Chuyển hướng trở lại chính trang này để xem kết quả
        return redirect('manage_rooms')

    # Lấy danh sách tất cả các phòng để hiển thị
    all_rooms = Room.objects.select_related('room_class').order_by('room_number')
    
    context = {
        'rooms': all_rooms,
        'room_statuses': Room.Status.choices # Gửi các lựa chọn trạng thái sang template
    }
    return render(request, 'booking/dashboard_rooms.html', context)

@user_passes_test(is_reception_staff)
def check_in_view(request, pk):
    """
    Xử lý quy trình Check-in: Gán một phòng trống cụ thể cho một đơn đặt phòng.
    """
    booking = get_object_or_404(Booking, pk=pk)
    
    # Tìm tất cả các phòng vật lý có sẵn thuộc đúng Hạng phòng mà khách đã đặt.
    available_rooms = Room.objects.filter(
        room_class=booking.room_class, 
        status=Room.Status.AVAILABLE
    )

    if request.method == 'POST':
        # Lấy ID của phòng đã được chọn từ form.
        selected_room_id = request.POST.get('selected_room')
        if selected_room_id:
            selected_room = get_object_or_404(Room, pk=selected_room_id)
            
            # --- CẬP NHẬT DATABASE ---
            # 1. Gán phòng cụ thể vào đơn hàng.
            booking.assigned_room = selected_room
            # 2. Cập nhật trạng thái đơn hàng thành "Đã nhận phòng".
            booking.status = Booking.Status.CHECKED_IN
            booking.save()
            
            # 3. Cập nhật trạng thái của phòng thành "Đang có khách".
            selected_room.status = Room.Status.OCCUPIED
            selected_room.save()
            
            messages.success(request, f"Check-in thành công cho đơn #{booking.id}. Đã gán phòng {selected_room.room_number}.")
            return redirect('manage_bookings')

    context = {
        'booking': booking,
        'available_rooms': available_rooms
    }
    return render(request, 'booking/dashboard_check_in.html', context)

@user_passes_test(is_reception_staff)
def check_out_view(request, pk):
    """
    Xử lý quy trình Check-out:
    - Cập nhật trạng thái Booking thành "Đã hoàn thành".
    - Cập nhật trạng thái Room thành "Cần dọn dẹp".
    """
    if request.method == 'POST':
        # Lấy đơn hàng cần check-out
        booking = get_object_or_404(Booking, pk=pk)
        
        # --- CẬP NHẬT DATABASE ---
        # 1. Cập nhật trạng thái đơn hàng
        booking.status = Booking.Status.COMPLETED
        booking.save()
        
        # 2. Cập nhật trạng thái phòng để bộ phận buồng phòng xử lý
        if booking.assigned_room:
            room = booking.assigned_room
            room.status = Room.Status.CLEANING
            room.save()
        
        messages.success(request, f"Check-out thành công cho đơn hàng #{booking.id}. Phòng {room.room_number} đã được chuyển sang trạng thái cần dọn dẹp.")
    
    return redirect('manage_bookings')
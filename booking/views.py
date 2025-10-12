from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import RoomType, RoomClass, Room, Service, PaymentProof, Booking
from .forms import BookingOptionsForm, CheckoutForm, PaymentProofForm
from datetime import datetime
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required

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
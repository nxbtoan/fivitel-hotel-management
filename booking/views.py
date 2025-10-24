from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required,  user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import RoomType, RoomClass, Room, Service, PaymentProof, Booking
from services.models import ServiceCategory
from .forms import BookingOptionsForm, CheckoutForm, PaymentProofForm, BookingEditForm
from datetime import timedelta, datetime

def homepage(request):
    """
    View cho trang chủ, lấy ra các loại phòng và loại dịch vụ nổi bật CÓ ẢNH.
    """
    # Lấy tối đa 4 loại phòng đầu tiên có trường 'image' không rỗng
    featured_room_types = RoomType.objects.exclude(image__isnull=True).exclude(image='').order_by('id')[:4]
    
    # Lấy tối đa 4 loại dịch vụ đầu tiên có trường 'image' không rỗng
    featured_service_categories = ServiceCategory.objects.exclude(image__isnull=True).exclude(image='').order_by('id')[:4]

    context = {
        'featured_room_types': featured_room_types,
        'featured_service_categories': featured_service_categories,
    }
    return render(request, 'homepage.html', context)

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
    View xử lý trang Checkout - Phiên bản hoàn chỉnh, an toàn và linh hoạt.
    - Hoạt động cho cả khách đã đăng nhập và khách vãng lai.
    - Chống lỗi đặt trùng phòng (race condition) bằng transaction.
    - Xử lý chuyển hướng thông minh dựa trên loại khách và phương thức thanh toán.
    """
    # --- PHẦN 1: LẤY DỮ LIỆU TỪ SESSION VÀ TÍNH TOÁN ---
    booking_options = request.session.get('booking_options')
    if not booking_options:
        messages.error(request, "Phiên đặt phòng đã hết hạn hoặc có lỗi xảy ra. Vui lòng thử lại.")
        return redirect('homepage')

    # Lấy thông tin cần thiết từ session
    room_class = get_object_or_404(RoomClass, pk=booking_options.get('room_class_id'))
    selected_services = Service.objects.filter(id__in=booking_options.get('service_ids', []))
    check_in = datetime.fromisoformat(booking_options.get('check_in')).date()
    check_out = datetime.fromisoformat(booking_options.get('check_out')).date()
    
    # Tính toán giá
    duration = (check_out - check_in).days if (check_out > check_in) else 0
    room_price = room_class.base_price * duration
    services_price = sum(service.price for service in selected_services)
    total_price = room_price + services_price

    # --- PHẦN 2: XỬ LÝ POST REQUEST (KHI NGƯỜI DÙNG NHẤN NÚT "HOÀN TẤT") ---
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            guest_data = form.cleaned_data
            try:
                # Sử dụng transaction để đảm bảo tất cả các thao tác DB hoặc thành công hoặc thất bại cùng lúc
                with transaction.atomic():
                    # Tìm một phòng trống và "khóa" các dòng đang truy vấn lại để tránh người khác đặt cùng lúc
                    if Room.objects.select_for_update().filter(room_class=room_class, status='AVAILABLE').count() == 0:
                        messages.error(request, 'Rất tiếc, hạng phòng này vừa hết phòng trống trong lúc bạn thao tác.')
                        return redirect('room_class_list', room_type_id=room_class.room_type.id)

                    # Chuẩn bị dữ liệu để tạo Booking
                    booking_details = {
                        'room_class': room_class,
                        'check_in_date': check_in,
                        'check_out_date': check_out,
                        'room_price': room_price,
                        'services_price': services_price,
                        'total_price': total_price,
                        'payment_method': guest_data.get('payment_method'),
                        'special_requests': guest_data.get('special_requests'),
                    }

                    # Xử lý thông tin khách hàng dựa trên việc đăng nhập và lựa chọn
                    if request.user.is_authenticated:
                        booking_details['customer'] = request.user
                        # Nếu người dùng đặt cho chính họ, lấy thông tin từ tài khoản
                        if guest_data.get('booking_for') == 'SELF':
                            booking_details.update({
                                'guest_full_name': request.user.full_name, 'guest_email': request.user.email,
                                'guest_phone_number': request.user.phone_number, 'guest_nationality': request.user.nationality,
                            })
                        else: # Nếu người dùng đặt cho người khác
                            booking_details.update({
                                'guest_full_name': guest_data.get('full_name'), 'guest_email': guest_data.get('email'),
                                'guest_phone_number': guest_data.get('phone_number'), 'guest_nationality': guest_data.get('nationality'),
                            })
                    else: # Khách vãng lai
                        booking_details.update({
                            'guest_full_name': guest_data.get('full_name'), 'guest_email': guest_data.get('email'),
                            'guest_phone_number': guest_data.get('phone_number'), 'guest_nationality': guest_data.get('nationality'),
                        })
                    
                    # Tạo bản ghi Booking mới
                    new_booking = Booking.objects.create(**booking_details)
                    new_booking.additional_services.set(selected_services)
                    
                    # Dọn dẹp session sau khi đã tạo đơn thành công
                    del request.session['booking_options']
                    
                    # --- LOGIC CHUYỂN HƯỚNG THÔNG MINH ---
                    is_bank_transfer = (new_booking.payment_method == 'BANK_TRANSFER')
                    
                    if request.user.is_authenticated:
                        if is_bank_transfer:
                            return redirect('payment_guidance', booking_pk=new_booking.pk)
                        else: # PAY_LATER
                            return redirect('booking_detail', pk=new_booking.pk)
                    else: # Khách vãng lai
                        if is_bank_transfer:
                            return redirect('guest_payment_guidance', booking_code=new_booking.booking_code)
                        else: # PAY_LATER
                            return redirect('guest_booking_detail', booking_code=new_booking.booking_code)

            except Exception as e:
                print(f"!!! LỖI BẤT NGỜ TRONG CHECKOUT: {type(e).__name__} - {e}")
                messages.error(request, f"Lỗi hệ thống không mong muốn: {e}")
                return redirect('homepage')
    
    # --- PHẦN 3: XỬ LÝ GET REQUEST HOẶC KHI POST THẤT BẠI ---
    else: # Đây là trường hợp GET request
        form = CheckoutForm() # Form trống cho khách vãng lai

    context = {
        'form': form,
        'room_class': room_class,
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
    Hiển thị trang hướng dẫn thanh toán cho NGƯỜI DÙNG ĐÃ ĐĂNG NHẬP.
    """
    booking = get_object_or_404(Booking, pk=booking_pk, customer=request.user)
    
    if booking.status != 'PENDING':
        messages.warning(request, "Đơn hàng này không cần thanh toán hoặc đã được xử lý.")
        return redirect('booking_detail', pk=booking.pk)
    
    # --- SỬA LỖI AttributeError Ở ĐÂY ---
    # Dùng try-except để xử lý trường hợp chưa có bằng chứng nào được tạo
    try:
        proof_instance = booking.payment_proof
    except PaymentProof.DoesNotExist:
        proof_instance = None # Nếu chưa có, instance là None

    if request.method == 'POST':
        # Truyền instance vào form để nó biết là tạo mới hay cập nhật
        form = PaymentProofForm(request.POST, request.FILES, instance=proof_instance)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.booking = booking
            proof.save()
            messages.success(request, "Đã tải lên bằng chứng thanh toán thành công.")
            return redirect('booking_detail', pk=booking.pk)
    else:
        form = PaymentProofForm(instance=proof_instance)

    context = {
        'booking': booking,
        'form': form
    }
    return render(request, 'booking/payment_guidance.html', context)

def guest_booking_detail_view(request, booking_code):
    """
    Hiển thị trang chi tiết đơn hàng cho khách vãng lai thông qua mã an toàn.
    """
    # Tìm đơn hàng bằng booking_code duy nhất, không cần kiểm tra user
    booking = get_object_or_404(Booking, booking_code=booking_code)
    
    context = {
        'booking': booking
    }
    # Chúng ta sẽ tạo một template mới cho trang này
    return render(request, 'booking/guest_booking_detail.html', context)


def guest_payment_guidance_view(request, booking_code):
    """
    Hiển thị trang hướng dẫn thanh toán và cho phép khách vãng lai
    tải lên bằng chứng thanh toán.
    """
    booking = get_object_or_404(Booking, booking_code=booking_code)

    if booking.status != 'PENDING':
        messages.warning(request, "Đơn hàng này không cần thanh toán hoặc đã được xử lý.")
        return redirect('guest_booking_detail', booking_code=booking.booking_code)

    try:
        proof_instance = booking.payment_proof
    except PaymentProof.DoesNotExist:
        proof_instance = None # Nếu chưa có, instance là None

    if request.method == 'POST':
        # Truyền instance vào form để nó biết là tạo mới hay cập nhật
        form = PaymentProofForm(request.POST, request.FILES, instance=proof_instance)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.booking = booking
            proof.save()
            messages.success(request, "Đã tải lên bằng chứng thanh toán thành công. Chúng tôi sẽ sớm xác nhận đơn hàng của bạn.")
            return redirect('guest_booking_detail', booking_code=booking.booking_code)
    else:
        form = PaymentProofForm(instance=proof_instance)

    context = {
        'booking': booking,
        'form': form
    }
    # Tái sử dụng template payment_guidance.html
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

@login_required
def edit_booking_view(request, pk):
    """
    Xử lý việc khách hàng chỉnh sửa đơn đặt hàng.
    Phiên bản nâng cấp: Dùng ModelForm chuyên dụng và tính toán lại giá.
    """
    # Lấy đúng đơn hàng của người dùng, đảm bảo an toàn
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)

    # Sử dụng property is_editable đã có sẵn trong model để kiểm tra
    if not booking.is_editable:
        messages.error(request, f"Đơn hàng #{booking.id} không còn có thể chỉnh sửa.")
        return redirect('booking_detail', pk=booking.pk)

    if request.method == 'POST':
        # Khởi tạo form với dữ liệu POST và liên kết với instance booking hiện tại
        form = BookingEditForm(request.POST, instance=booking)
        if form.is_valid():
            # Bước 1: Lưu các thay đổi (thông tin khách, dịch vụ) vào database
            # ModelForm sẽ tự động xử lý việc cập nhật ManyToManyField
            form.save()

            # Bước 2: Tải lại instance booking từ DB để có danh sách services mới nhất
            booking.refresh_from_db()

            # Bước 3: Tính toán lại tổng tiền dựa trên các thay đổi
            num_nights = (booking.check_out_date - booking.check_in_date).days
            room_price = booking.room_class.base_price * num_nights
            services_price = sum(service.price for service in booking.additional_services.all())
            booking.total_price = room_price + services_price

            # Bước 4: Đặt lại trạng thái để lễ tân xác nhận lại (quan trọng!)
            booking.status = Booking.Status.PENDING
            
            # Lưu lại lần cuối cùng với tổng tiền và trạng thái mới
            booking.save()

            messages.success(request, f"Đơn hàng #{booking.id} đã được cập nhật. Vui lòng chờ lễ tân xác nhận lại.")
            return redirect('booking_detail', pk=booking.pk)
    else:
        # Khi mới vào trang (GET), khởi tạo form với dữ liệu của instance booking
        form = BookingEditForm(instance=booking)

    context = {
        'form': form,
        'booking': booking,
    }
    # Render ra một template mới dành riêng cho việc chỉnh sửa
    return render(request, 'booking/edit_booking.html', context)

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

@user_passes_test(is_reception_staff)
def staff_booking_detail_view(request, pk):
    """
    Hiển thị trang chi tiết đơn đặt phòng dành cho nhân viên (Lễ tân, Admin).
    """
    # Lấy đơn hàng và các thông tin liên quan để tối ưu truy vấn
    booking = get_object_or_404(
        Booking.objects.select_related(
            'room_class', 'customer', 'assigned_room', 'payment_proof'
        ).prefetch_related('additional_services'), 
        pk=pk
    )
    
    context = {
        'booking': booking
    }
    return render(request, 'booking/dashboard_booking_detail.html', context)

@login_required
def edit_booking_view(request, pk):
    """
    Xử lý việc chỉnh sửa một đơn đặt phòng đã có.
    """
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)

    # Nếu đơn hàng không còn được phép sửa, chuyển hướng về danh sách
    if not booking.is_editable:
        messages.error(request, "Đơn đặt phòng này không thể chỉnh sửa.")
        return redirect('my_bookings')

    if request.method == 'POST':
        # Khởi tạo form với dữ liệu mới gửi lên
        form = BookingOptionsForm(request.POST)
        if form.is_valid():
            options = form.cleaned_data
            
            # Cập nhật lại các thông tin trên đơn hàng
            booking.check_in_date = options['check_in_date']
            booking.check_out_date = options['check_out_date']
            
            # Tính toán lại tổng tiền
            duration = (booking.check_out_date - booking.check_in_date).days
            room_price = booking.room_class.base_price * duration
            services_price = sum(service.price for service in options['additional_services'])
            booking.total_price = room_price + services_price
            
            # Lưu lại đơn hàng
            booking.save()
            
            # Cập nhật lại các dịch vụ đi kèm
            booking.additional_services.set(options['additional_services'])

            messages.success(request, f"Đã cập nhật thành công đơn hàng #{booking.id}.")
            return redirect('my_bookings')
    else:
        # Khi mới vào trang, tạo form và điền sẵn dữ liệu từ đơn hàng cũ
        initial_data = {
            'check_in_date': booking.check_in_date,
            'check_out_date': booking.check_out_date,
            'additional_services': booking.additional_services.all(),
            # Giả sử số khách không đổi, bạn có thể thêm các trường này nếu muốn
            # 'adults': booking.adults, 
        }
        form = BookingOptionsForm(initial=initial_data)

    context = {
        'form': form,
        'booking': booking,
        # Lấy lại hạng phòng để hiển thị thông tin và tính tiền bằng JS
        'room_class': booking.room_class 
    }
    # Tái sử dụng template của trang Tùy chọn đặt phòng
    return render(request, 'booking/booking_options.html', context)

def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin để đảm bảo chỉ Admin mới có thể truy cập."""
    def test_func(self):
        return is_admin(self.request.user)

class RoomTypeListView(AdminRequiredMixin, ListView):
    """View hiển thị danh sách tất cả các Loại phòng."""
    model = RoomType
    template_name = 'booking/dashboard_roomtype_list.html'
    context_object_name = 'room_types'

class RoomTypeCreateView(AdminRequiredMixin, CreateView):
    """View hiển thị form để tạo mới một Loại phòng."""
    model = RoomType
    template_name = 'booking/dashboard_roomtype_form.html'
    fields = ['name', 'description', 'image']
    success_url = reverse_lazy('room_type_list')

class RoomTypeUpdateView(AdminRequiredMixin, UpdateView):
    """View hiển thị form để chỉnh sửa một Loại phòng."""
    model = RoomType
    template_name = 'booking/dashboard_roomtype_form.html'
    fields = ['name', 'description', 'image']
    success_url = reverse_lazy('room_type_list')

class RoomTypeDeleteView(AdminRequiredMixin, DeleteView):
    """View xử lý việc xóa một Loại phòng."""
    model = RoomType
    success_url = reverse_lazy('room_type_list')

class RoomClassListView(AdminRequiredMixin, ListView):
    """View hiển thị danh sách tất cả các Hạng phòng."""
    model = RoomClass
    template_name = 'booking/dashboard_roomclass_list.html'
    context_object_name = 'room_classes'

class RoomClassCreateView(AdminRequiredMixin, CreateView):
    """View hiển thị form để tạo mới một Hạng phòng."""
    model = RoomClass
    template_name = 'booking/dashboard_roomclass_form.html'
    fields = ['room_type', 'name', 'description', 'base_price', 'area', 'amenities', 'image']
    success_url = reverse_lazy('room_class_list_admin') # Đổi tên để tránh trùng lặp

class RoomClassUpdateView(AdminRequiredMixin, UpdateView):
    """View hiển thị form để chỉnh sửa một Hạng phòng."""
    model = RoomClass
    template_name = 'booking/dashboard_roomclass_form.html'
    fields = ['room_type', 'name', 'description', 'base_price', 'area', 'amenities', 'image']
    success_url = reverse_lazy('room_class_list_admin')

class RoomClassDeleteView(AdminRequiredMixin, DeleteView):
    """View xử lý việc xóa một Hạng phòng."""
    model = RoomClass
    success_url = reverse_lazy('room_class_list_admin')

class RoomListView(AdminRequiredMixin, ListView):
    """View hiển thị danh sách tất cả các phòng vật lý."""
    model = Room
    template_name = 'booking/dashboard_room_list.html'
    context_object_name = 'rooms'

class RoomCreateView(AdminRequiredMixin, CreateView):
    """View hiển thị form để tạo mới một phòng."""
    model = Room
    template_name = 'booking/dashboard_room_form.html'
    fields = ['room_class', 'room_number', 'status']
    success_url = reverse_lazy('room_list_admin')

class RoomUpdateView(AdminRequiredMixin, UpdateView):
    """View hiển thị form để chỉnh sửa một phòng."""
    model = Room
    template_name = 'booking/dashboard_room_form.html'
    fields = ['room_class', 'room_number', 'status']
    success_url = reverse_lazy('room_list_admin')

class RoomDeleteView(AdminRequiredMixin, DeleteView):
    """View xử lý việc xóa một phòng."""
    model = Room
    success_url = reverse_lazy('room_list_admin')
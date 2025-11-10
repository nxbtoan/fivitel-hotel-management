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

# ==============================================================================
# PHẦN 1: CÁC VIEW CÔNG KHAI (PUBLIC VIEWS)
# Dành cho khách vãng lai, trang chủ và luồng đặt phòng
# ==============================================================================
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

    # 1. Lấy thông tin tìm kiếm từ URL
    check_in_str = request.GET.get('check_in')
    check_out_str = request.GET.get('check_out')
    adults = int(request.GET.get('adults', 1)) # Mặc định là 1 người lớn
    children = int(request.GET.get('children', 0)) # Mặc định là 0 trẻ em
    total_guests = adults + children

    # 2. Lọc cơ bản: Lấy các hạng phòng thuộc loại này VÀ có đủ sức chứa
    room_classes = room_type.classes.filter(
        max_occupancy__gte=total_guests
    ).annotate(
        total_rooms_count=Count('rooms')
    )

    # 3. Lọc nâng cao (Nếu có ngày):
    if check_in_str and check_out_str:
        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()

            if check_in >= check_out:
                raise ValueError("Ngày trả phòng phải sau ngày nhận phòng")

            # Định nghĩa các đơn hàng bị trùng lặp (overlap)
            overlap_filter = (
                Q(booking__check_in_date__lt=check_out) &
                Q(booking__check_out_date__gt=check_in) &
                ~Q(booking__status__in=[Booking.Status.CANCELLED, Booking.Status.EXPIRED])
            )

            # Đếm số phòng đã bị đặt trong khoảng ngày đó
            room_classes = room_classes.annotate(
                booked_rooms_count=Count('booking', filter=overlap_filter)
            ).annotate(
                # Tính số phòng còn trống = Tổng - Đã đặt
                available_rooms_count=F('total_rooms_count') - F('booked_rooms_count')
            )
            
        except (ValueError, TypeError):
            # Nếu ngày không hợp lệ, quay về logic đếm phòng "AVAILABLE" cơ bản
            messages.error(request, "Ngày không hợp lệ. Vui lòng chọn lại.")
            room_classes = room_classes.annotate(
                available_rooms_count=Count('rooms', filter=Q(rooms__status='AVAILABLE'))
            )
    else:
        # Nếu không có ngày, chỉ đếm số phòng có status 'AVAILABLE'
        room_classes = room_classes.annotate(
            available_rooms_count=Count('rooms', filter=Q(rooms__status='AVAILABLE'))
        )

    # Xử lý chuỗi tiện ích (Giữ nguyên)
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
    View xử lý trang Checkout
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
        form = CheckoutForm(request.POST, request=request)
        if form.is_valid():
            guest_data = form.cleaned_data
            try:
                with transaction.atomic():
                    # 1. Kiểm tra phòng trống
                    if Room.objects.select_for_update().filter(room_class=room_class, status='AVAILABLE').count() == 0:
                        messages.error(request, 'Rất tiếc, hạng phòng này vừa hết phòng trống trong lúc bạn thao tác.')
                        return redirect('room_class_list', room_type_id=room_class.room_type.id)

                    # 2. Chuẩn bị dữ liệu để tạo Booking
                    booking_details = {
                        'room_class': room_class,
                        'check_in_date': check_in,
                        'check_out_date': check_out,
                        'adults': booking_options.get('adults'), # Lấy từ session
                        'children': booking_options.get('children'), # Lấy từ session
                        'room_price': room_price,
                        'services_price': services_price,
                        'total_price': total_price,
                        'payment_method': guest_data.get('payment_method'),
                        'special_requests': guest_data.get('special_requests'),
                    }

                    # 3. Xử lý thông tin khách hàng
                    if request.user.is_authenticated:
                        booking_details['customer'] = request.user
                        if guest_data.get('booking_for') == 'SELF':
                            booking_details.update({
                                'guest_full_name': request.user.full_name or request.user.username,
                                'guest_email': request.user.email,
                                'guest_phone_number': request.user.phone_number,
                                'guest_nationality': request.user.nationality,
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
                    
                    # 4. Tạo bản ghi Booking mới (CHỈ 1 LẦN)
                    new_booking = Booking.objects.create(**booking_details)
                    new_booking.additional_services.set(selected_services)

                    # 5. Phân loại và khóa đơn (LOGIC MỚI CỦA BẠN)
                    time_until_checkin = new_booking.check_in_date - timezone.now().date()
                    is_urgent_booking = time_until_checkin < timedelta(days=1)

                    if is_urgent_booking:
                        # Đơn đặt gấp (< 24h)
                        new_booking.is_locked = True
                        new_booking.status = Booking.Status.PENDING_PAYMENT
                        new_booking.save()
                        
                        new_booking.send_booking_email(
                            subject=f"Yêu cầu Thanh toán Gấp cho Đơn hàng #{new_booking.id}",
                            template_name='emails/urgent_payment_required.html'
                        )
                        messages.warning(request, "Đây là đơn đặt gấp (nhận phòng trong 24h). Vui lòng thanh toán ngay để xác nhận giữ phòng.")
                        
                        # Xác định URL chuyển hướng
                        redirect_url_name = 'payment_guidance'
                        args = {'booking_pk': new_booking.pk}
                        if not request.user.is_authenticated:
                            redirect_url_name = 'guest_payment_guidance'
                            args = {'booking_code': new_booking.booking_code}

                    else:
                        # Đơn đặt sớm (>= 24h)
                        new_booking.is_locked = False
                        new_booking.status = Booking.Status.PENDING_REVIEW
                        new_booking.save()
                        
                        new_booking.send_booking_email(
                            subject=f"Fivitel đã nhận Đơn hàng #{new_booking.id} của bạn",
                            template_name='emails/booking_received.html'
                        )
                        
                        # Xác định URL chuyển hướng
                        redirect_url_name = 'booking_detail'
                        args = {'pk': new_booking.pk}
                        if not request.user.is_authenticated:
                            redirect_url_name = 'guest_booking_detail'
                            args = {'booking_code': new_booking.booking_code}

                    # 6. Dọn dẹp session
                    del request.session['booking_options']

                    # 7. Chuyển hướng
                    return redirect(redirect_url_name, **args)
            
            except Exception as e:
                # Bắt lỗi nếu có bất kỳ vấn đề gì xảy ra
                print(f"!!! LỖI BẤT NGỜ TRONG CHECKOUT: {type(e).__name__} - {e}")
                messages.error(request, f"Lỗi hệ thống không mong muốn. Vui lòng thử lại. Lỗi: {e}")
                return redirect('homepage')
        
        else:
            pass
    
    # --- PHẦN 3: XỬ LÝ GET REQUEST HOẶC KHI POST THẤT BẠI ---
    else: 
        form = CheckoutForm(request=request)

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

    if (booking.status == Booking.Status.PENDING_PAYMENT and 
        timezone.now() > booking.created_at + timedelta(hours=2)):

        booking.status = Booking.Status.EXPIRED
        booking.save()
        messages.error(request, "Đơn đặt phòng của bạn đã hết hạn do chưa thanh toán kịp thời.")
        return redirect('guest_booking_detail', booking_code=booking.booking_code)
    
    if not booking.is_payment_ready:
        messages.warning(request, "Đơn hàng này không cần thanh toán hoặc đã được xử lý.")
        return redirect('guest_booking_detail', booking_code=booking.booking_code)

    try:
        proof_instance = booking.payment_proof
    except PaymentProof.DoesNotExist:
        proof_instance = None # Nếu chưa có, instance là None

    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES, instance=proof_instance)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.booking = booking
            proof.save()
            booking.status = Booking.Status.PAYMENT_PENDING_VERIFICATION
            booking.payment_date = timezone.now()
            booking.save()
            messages.success(request, "Đã tải lên bằng chứng thanh toán thành công.")
            booking.send_booking_email(
                subject=f"Đã nhận chứng từ thanh toán cho Đơn hàng #{booking.id}",
                template_name='emails/payment_verifying.html'
            )
            return redirect('guest_booking_detail', booking_code=booking.booking_code)
    else:
        form = PaymentProofForm(instance=proof_instance)

    context = {
        'booking': booking,
        'form': form
    }

    return render(request, 'booking/payment_guidance.html', context)

# ==============================================================================
# PHẦN 2: CÁC VIEW CỦA KHÁCH HÀNG (CUSTOMER VIEWS)
# Yêu cầu @login_required
# ==============================================================================
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
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)
    # Tự động khóa đơn nếu cần, trước khi render
    check_and_lock_booking(booking)
    
    context = {
        'booking': booking
    }
    return render(request, 'booking/booking_detail.html', context)

@login_required
def payment_guidance_view(request, booking_pk):
    booking = get_object_or_404(Booking, pk=booking_pk, customer=request.user)
    
    # --- KIỂM TRA HẾT HẠN ĐƠN GẤP ---
    if (booking.status == Booking.Status.PENDING_PAYMENT and 
        timezone.now() > booking.created_at + timedelta(hours=2)):
        
        booking.status = Booking.Status.EXPIRED
        booking.save()
        messages.error(request, "Đơn đặt phòng của bạn đã hết hạn do chưa thanh toán kịp thời.")
        return redirect('booking_detail', pk=booking.pk)
    
    # Chỉ cho phép thanh toán ở các trạng thái này
    if not booking.is_payment_ready:
        messages.warning(request, "Đơn hàng này không cần thanh toán hoặc đã được xử lý.")
        return redirect('booking_detail', pk=booking.pk)
    
    try:
        proof_instance = booking.payment_proof
    except PaymentProof.DoesNotExist:
        proof_instance = None 

    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES, instance=proof_instance)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.booking = booking
            proof.save()
            
            # --- CẬP NHẬT SAU KHI UPLOAD ---
            booking.status = Booking.Status.PAYMENT_PENDING_VERIFICATION
            booking.payment_date = timezone.now()
            booking.save()
            
            messages.success(request, "Đã tải lên bằng chứng thanh toán. Vui lòng chờ kế toán xác nhận.")
            
            # Gửi mail thông báo đã nhận chứng từ
            booking.send_booking_email(
                subject=f"Đã nhận chứng từ thanh toán cho Đơn hàng #{booking.id}",
                template_name='emails/payment_verifying.html' # (Cần tạo template này)
            )
            
            return redirect('booking_detail', pk=booking.pk)
    else:
        form = PaymentProofForm(instance=proof_instance)

    context = { 'booking': booking, 'form': form }
    return render(request, 'booking/payment_guidance.html', context)

@login_required
def edit_booking_view(request, pk):
    """
    Xử lý việc khách hàng chỉnh sửa đơn đặt hàng.
    """
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)

    # --- KIỂM TRA KHÓA ---
    if check_and_lock_booking(booking):
        messages.error(request, f"Đơn hàng #{booking.id} đã bị khóa và không thể chỉnh sửa.")
        return redirect('booking_detail', pk=booking.pk)

    if request.method == 'POST':
        # Khởi tạo form với dữ liệu POST và liên kết với instance booking hiện tại
        form = BookingEditForm(request.POST, instance=booking)
        if form.is_valid():
            # Bước 1: Lưu các thay đổi (thông tin khách, dịch vụ) vào database
            form.save()

            # Bước 2: Tải lại instance booking từ DB để có danh sách services mới nhất
            booking.refresh_from_db()

            # Bước 3: Tính toán lại tổng tiền dựa trên các thay đổi
            num_nights = (booking.check_out_date - booking.check_in_date).days
            room_price = booking.room_class.base_price * num_nights
            services_price = sum(service.price for service in booking.additional_services.all())

            booking.total_price = room_price + services_price
            booking.room_price = room_price
            booking.services_price = services_price

            # Bước 4: Đặt lại trạng thái để lễ tân xác nhận lại (quan trọng!)
            booking.status = Booking.Status.PENDING_REVIEW
            
            # Lưu lại lần cuối cùng với tổng tiền và trạng thái mới
            booking.save()

            messages.success(request, f"Đơn hàng #{booking.id} đã được cập nhật.")
            return redirect('booking_detail', pk=booking.pk)
    else:
        form = BookingEditForm(instance=booking)

    context = {
        'form': form,
        'booking': booking,
    }
    # Render ra một template mới dành riêng cho việc chỉnh sửa
    return render(request, 'booking/edit_booking.html', context)

@login_required
def cancel_booking_view(request, pk):
    """
    Xử lý yêu cầu hủy đơn đặt phòng của khách hàng.
    Chỉ cho phép hủy nếu ngày check-in còn hơn 24 giờ.
    """
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)
    
    if request.method == 'POST' and booking.is_cancellable:
        booking.status = Booking.Status.CANCELLED
        booking.is_locked = True
        booking.save()
        messages.success(request, "Đã hủy đơn hàng thành công.")
    else:
        messages.error(request, "Không thể hủy đơn hàng này. Đơn đã bị khóa hoặc đã qua thời hạn cho phép.")
    
    return redirect('my_bookings')

# ==============================================================================
# PHẦN 3: HÀM HỖ TRỢ & MIXINS (HELPER FUNCTIONS)
# Hàm kiểm tra logic và quyền
# ==============================================================================
def check_and_lock_booking(booking):
    """
    Kiểm tra đơn hàng, nếu quá hạn sửa (2h) hoặc sắp đến ngày check-in,
    tự động khóa đơn hàng và cập nhật trạng thái.
    Trả về True nếu đơn bị khóa, False nếu không.
    """
    if booking.is_locked:
        return True # Đã khóa rồi, không cần làm gì

    now = timezone.now()
    # YÊU CẦU MỚI: Giới hạn sửa là 2 GIỜ
    is_over_edit_time = now > (booking.created_at + timedelta(hours=2))
    is_checkin_today_or_past = now.date() >= booking.check_in_date
    
    # Chỉ áp dụng cho đơn đặt sớm đang chờ review
    if booking.status == Booking.Status.PENDING_REVIEW and (is_over_edit_time or is_checkin_today_or_past):
        booking.is_locked = True
        booking.save()
        
        # Gửi mail thông báo đơn đã chốt, mời thanh toán
        booking.send_booking_email(
            subject=f"Đơn hàng #{booking.id} đã hết hạn chỉnh sửa",
            template_name='emails/booking_locked.html'
        )
        return True
        
    return False

def is_reception_staff(user):
    return user.is_authenticated and (user.role in ['RECEPTION', 'ADMIN'])

def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin để đảm bảo chỉ Admin mới có thể truy cập."""
    def test_func(self):
        return is_admin(self.request.user)
    
# ==============================================================================
# PHẦN 4: CÁC VIEW CỦA DASHBOARD (STAFF/ADMIN VIEWS)
# Yêu cầu @user_passes_test hoặc AdminRequiredMixin
# ==============================================================================

# ===== 1. Logic Quản lý Booking (Staff) =====
@user_passes_test(is_reception_staff)
def check_in_booking_view(request, pk):
    """
    Xử lý hành động 'Xác nhận Check-in' sau khi phòng đã được gán.
    """
    if request.method == 'POST':
        booking = get_object_or_404(Booking, pk=pk)
        
        # Chỉ check-in được nếu đơn đã CONFIRMED (đã gán phòng)
        if booking.status == Booking.Status.CONFIRMED and booking.assigned_room:
            booking.status = Booking.Status.CHECKED_IN
            booking.save()
            
            # Cập nhật trạng thái phòng
            room = booking.assigned_room
            room.status = Room.Status.OCCUPIED
            room.save()
            
            messages.success(request, f"Đã xác nhận check-in cho khách vào phòng {room.room_number}.")
        else:
            messages.error(request, "Không thể check-in. Đơn hàng chưa được gán phòng hoặc đang ở trạng thái không hợp lệ.")
            
    return redirect('manage_bookings')

@user_passes_test(is_reception_staff)
def manage_bookings_view(request):
    """
    Hiển thị trang quản lý tất cả đơn đặt phòng cho Lễ tân.
    Cho phép lọc đơn hàng theo trạng thái.
    """
    status_filter = request.GET.get('status')
    
    # Bắt đầu với việc lấy tất cả đơn hàng, sắp xếp mới nhất lên đầu
    # Dùng select_related và prefetch_related để tối ưu truy vấn database
    bookings = Booking.objects.select_related(
        'room_class', 'customer'
    ).prefetch_related(
        'payment_proof'
    ).order_by('-created_at')

    if status_filter:
        if status_filter == 'PENDING_ALL':
            # "Chờ xử lý" = (Đang review HOẶC Đặt gấp)
            bookings = bookings.filter(status__in=[
                Booking.Status.PENDING_REVIEW, 
                Booking.Status.PENDING_PAYMENT,
                Booking.Status.READY_FOR_PAYMENT
            ])
        elif status_filter == 'PAID_ALL':
            # "Đã thanh toán" = (Đã trả tiền HOẶC Đã gán phòng)
            bookings = bookings.filter(status__in=[
                Booking.Status.PAID, 
                Booking.Status.CONFIRMED
            ])
        elif status_filter == 'CANCELLED_ALL':
            # "Đã hủy" = (Khách hủy HOẶC Hết hạn)
             bookings = bookings.filter(status__in=[
                Booking.Status.CANCELLED, 
                Booking.Status.EXPIRED
            ])
        elif status_filter in Booking.Status.values:
            # Lọc theo các trạng thái riêng lẻ (CHECKED_IN, COMPLETED, v.v.)
            bookings = bookings.filter(status=status_filter)

    context = {
        'bookings': bookings,
        'current_filter': status_filter 
    }
    return render(request, 'booking/dashboard_bookings.html', context)

@user_passes_test(is_reception_staff)
def confirm_booking_view(request, pk):
    """
    Xử lý hành động 'Xác nhận' đơn hàng.
    """
    if request.method == 'POST':
        booking = get_object_or_404(Booking, pk=pk)
        
        if booking.status == Booking.Status.PAYMENT_PENDING_VERIFICATION:
            booking.status = Booking.Status.PAID 
            booking.save()
            messages.success(request, f"Đã xác nhận thanh toán cho đơn hàng #{booking.id}.")
            
            booking.send_booking_email(subject="Xác nhận Thanh toán Thành công", template_name='emails/payment_confirmed.html')
        else:
            messages.error(request, "Đơn hàng không ở trạng thái 'Chờ xác nhận TT' nên không thể thực hiện.")
            
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
def check_in_view(request, pk):
    """
    Xử lý quy trình Check-in: Gán một phòng trống cụ thể cho một đơn đặt phòng.
    """
    booking = get_object_or_404(Booking, pk=pk)

    if booking.status != Booking.Status.PAID:
        messages.error(request, "Chỉ có thể gán phòng cho các đơn hàng đã thanh toán (PAID).")
        return redirect('manage_bookings')
    
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
            booking.status = Booking.Status.CONFIRMED
            booking.save()
            
            messages.success(request, f"Đã gán phòng {selected_room.room_number} cho đơn #{booking.id}. Đơn hàng chuyển sang 'Đã xác nhận'.")
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

# ===== 2. Logic Quản lý Phòng (Staff) =====
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

# ===== 3. Logic Quản lý Cấu hình (Admin) =====
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
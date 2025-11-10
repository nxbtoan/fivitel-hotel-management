from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import OuterRef, Subquery
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .forms import ConsultationRequestForm, TicketResponseForm, CustomerResponseForm, ComplaintForm, TicketEditForm, ComplaintResolutionForm
from .models import Ticket, TicketResponse, CustomUser

# ==============================================================================
# VIEWS DÀNH CHO KHÁCH HÀNG (USER-FACING)
# ==============================================================================
def consultation_request_view(request):
    """
    Xử lý trang gửi Yêu cầu Tư vấn cho cả khách vãng lai và người đã đăng nhập.
    - Xử lý phương thức GET: Hiển thị form trống (hoặc điền sẵn thông tin nếu đã đăng nhập).
    - Xử lý phương thức POST: Xác thực dữ liệu và tạo một Ticket mới.
    - Hiển thị pop-up thông báo thành công sau khi gửi.
    """
    # Xử lý khi người dùng gửi form
    if request.method == 'POST':
        form = ConsultationRequestForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # Chuẩn bị dữ liệu để tạo Ticket
            ticket_details = {
                'type': data['request_type'],
                'description': data['content'],
                'status': Ticket.Status.NEW,
            }

            # Gán thông tin khách hàng
            if request.user.is_authenticated:
                ticket_details['customer'] = request.user
            else:
                ticket_details.update({
                    'guest_full_name': data['full_name'],
                    'guest_email': data['email'],
                    'guest_phone_number': data['phone_number'],
                })

            Ticket.objects.create(**ticket_details)

            success_url_list = None
            if request.user.is_authenticated:
                success_url_list = reverse('my_requests')

            return JsonResponse({
                'success': True,
                'is_guest': not request.user.is_authenticated,
                'home_url': reverse('homepage'),
                'success_url_list': success_url_list
            })
        
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    else: # Khi người dùng mới truy cập (GET)
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'full_name': request.user.full_name,
                'email': request.user.email,
                'phone_number': request.user.phone_number,
            }
        form = ConsultationRequestForm(initial=initial_data)

    context = {
        'form': form,
    }
    return render(request, 'crm/consultation_request.html', context)

@login_required
def my_requests_view(request):
    """Hiển thị danh sách CHỈ các Yêu cầu Tư vấn của khách hàng."""
    
    # Lấy phản hồi cuối cùng (tương tự logic nâng cấp trước)
    latest_response_message = TicketResponse.objects.filter(ticket=OuterRef('pk')).order_by('-created_at').values('message')[:1]
    latest_responder_name = TicketResponse.objects.filter(ticket=OuterRef('pk')).order_by('-created_at').values('responder__full_name')[:1]

    # Lọc các loại KHÔNG PHẢI là Khiếu nại
    tickets = Ticket.objects.filter(
        customer=request.user
    ).exclude(
        type=Ticket.Type.COMPLAINT 
    ).annotate(
        last_response_message=Subquery(latest_response_message),
        last_responder_name=Subquery(latest_responder_name)
    ).order_by('-created_at')

    context = {
        'tickets': tickets,
        'page_title': 'Các Yêu cầu Tư vấn', # Tiêu đề động
        'page_subtitle': 'Theo dõi lịch sử các yêu cầu tư vấn và hỗ trợ của bạn.' # Phụ đề động
    }
    # Tái sử dụng template my_tickets.html
    return render(request, 'crm/my_tickets.html', context)

@login_required
def my_complaints_view(request):
    """
    Hiển thị danh sách CHỈ các Khiếu nại của khách hàng.
    """
    
    latest_response_message = TicketResponse.objects.filter(ticket=OuterRef('pk')).order_by('-created_at').values('message')[:1]
    latest_responder_name = TicketResponse.objects.filter(ticket=OuterRef('pk')).order_by('-created_at').values('responder__full_name')[:1]
    
    # Chỉ lọc các loại là Khiếu nại
    tickets = Ticket.objects.filter(
        customer=request.user,
        type=Ticket.Type.COMPLAINT
    ).annotate(
        last_response_message=Subquery(latest_response_message),
        last_responder_name=Subquery(latest_responder_name)
    ).order_by('-created_at')

    context = {
        'tickets': tickets,
        'page_title': 'Các Khiếu nại của tôi', # Tiêu đề động
        'page_subtitle': 'Theo dõi lịch sử các khiếu nại đã gửi của bạn.' # Phụ đề động
    }
    return render(request, 'crm/my_tickets.html', context)

@login_required
def customer_ticket_detail_view(request, pk):
    """
    Hiển thị chi tiết một yêu cầu cho khách hàng và xử lý việc họ gửi trả lời.
    """
    ticket = get_object_or_404(Ticket, pk=pk, customer=request.user)
    responses = ticket.responses.select_related('responder').order_by('created_at')

    # Kiểm tra quyền chỉnh sửa (chỉ trong 1h, chưa RESOLVED, và là tư vấn)
    time_limit = timedelta(hours=1)
    can_edit = (
        ticket.type == Ticket.Type.CONSULTATION
        and ticket.status != Ticket.Status.RESOLVED
        and (timezone.now() - ticket.created_at) < time_limit
    )

    # Form mặc định (dù GET hay POST vẫn cần)
    reply_form = CustomerResponseForm()
    edit_form = TicketEditForm(instance=ticket)

    if request.method == 'POST':
        # 1️. GỬI TRẢ LỜI MỚI
        if 'submit_reply' in request.POST:
            reply_form = CustomerResponseForm(request.POST)
            if reply_form.is_valid():
                response = reply_form.save(commit=False)
                response.ticket = ticket
                response.responder = request.user
                response.save()
                ticket.status = Ticket.Status.AWAITING_STAFF_RESPONSE
                ticket.save()
                messages.success(request, "Đã gửi trả lời thành công.")
                return redirect('customer_ticket_detail', pk=ticket.pk)

        # 2. LƯU CHỈNH SỬA NỘI DUNG GỐC
        elif 'submit_edit' in request.POST and can_edit:
            edit_form = TicketEditForm(request.POST, instance=ticket)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, "Đã cập nhật yêu cầu thành công.")
                return redirect('customer_ticket_detail', pk=ticket.pk)

    # Luôn có context để render (kể cả khi GET)
    context = {
        'ticket': ticket,
        'responses': responses,
        'reply_form': reply_form,
        'edit_form': edit_form,
        'can_edit': can_edit,
    }
    return render(request, 'crm/customer_ticket_detail.html', context)

# ==============================================================================
# VIEWS DÀNH CHO NHÂN VIÊN (DASHBOARD)
# ==============================================================================
def is_crm_staff(user):
    """
    Hàm kiểm tra quyền, trả về True nếu user là CSKH hoặc Admin.
    """
    return user.is_authenticated and (user.role in ['RECEPTION', 'SUPPORT', 'ADMIN'])

def is_admin(user):
    """Kiểm tra xem user có phải là Admin không."""
    return user.is_authenticated and user.role == 'ADMIN'

@user_passes_test(is_crm_staff)
def manage_requests_view(request):
    """
    Hiển thị trang quản lý các yêu cầu (KHÔNG bao gồm Khiếu nại).
    """
    status_filter = request.GET.get('status')

    base_query = Ticket.objects.exclude(type=Ticket.Type.COMPLAINT)

    if request.user.role == 'RECEPTION':
        # Lễ tân: Chỉ thấy "Hỗ trợ Đặt phòng"
        tickets = base_query.filter(type=Ticket.Type.BOOKING_SUPPORT)
        
    elif request.user.role == 'SUPPORT':
        # CSKH: Thấy các loại tư vấn khác (KHÔNG thấy Đặt phòng)
        tickets = base_query.exclude(type=Ticket.Type.BOOKING_SUPPORT)
        
    elif request.user.role == 'ADMIN':
        # Admin: Thấy tất cả yêu cầu
        tickets = base_query
    
    else:
        # Dự phòng (nếu có vai trò lạ)
        tickets = Ticket.objects.none()

    tickets = tickets.select_related('customer', 'assigned_to').order_by('-created_at')
    
    # Logic lọc trạng thái
    if status_filter in Ticket.Status.values:
        tickets = tickets.filter(status=status_filter)

    context = {
        'tickets': tickets,
        'current_filter': status_filter,
        'ticket_statuses': Ticket.Status.choices,
        'header_title': 'Quản lý Yêu cầu',
        'back_url_to_dashboard': True
    }

    return render(request, 'crm/dashboard_tickets.html', context)

@user_passes_test(is_crm_staff)
def manage_complaints_view(request):
    """
    Hiển thị trang quản lý chỉ các KHIẾU NẠI.
    """
    status_filter = request.GET.get('status')

    if request.user.role == 'RECEPTION':
        # Lễ tân không có quyền xem khiếu nại
        messages.error(request, "Bạn không có quyền truy cập trang này.")
        return redirect('staff_dashboard')
    
    # CSKH và Admin sẽ thấy tất cả Khiếu nại
    tickets = Ticket.objects.filter(type=Ticket.Type.COMPLAINT).select_related('customer', 'assigned_to').order_by('-created_at')

    # Lấy danh sách nhân viên CSKH để tự "Nhận việc"
    staff_members = CustomUser.objects.filter(role='SUPPORT', is_active=True)

    if status_filter in Ticket.Status.values:
        tickets = tickets.filter(status=status_filter)

    context = {
        'tickets': tickets,
        'current_filter': status_filter,
        'ticket_statuses': Ticket.Status.choices,
        'header_title': 'Quản lý Khiếu nại',
        'staff_members': staff_members,
        'back_url_to_dashboard': True
    }
    return render(request, 'crm/dashboard_tickets.html', context)

@user_passes_test(is_crm_staff)
def ticket_detail_view(request, pk):
    """
    Hiển thị chi tiết một yêu cầu và xử lý phản hồi.
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    user_role = request.user.role

    # 1. Nếu là KHIẾU NẠI (COMPLAINT)
    if ticket.type == Ticket.Type.COMPLAINT:
        if user_role == 'RECEPTION':
            messages.error(request, "Lễ tân không có quyền xem Khiếu nại.")
            return redirect('staff_dashboard')
            
    # 2. Nếu là YÊU CẦU TƯ VẤN (CONSULTATION)
    else:
        if (user_role == 'RECEPTION' and ticket.type != Ticket.Type.BOOKING_SUPPORT):
            messages.error(request, "Bạn chỉ có quyền xem các yêu cầu Hỗ trợ Đặt phòng.")
            return redirect('manage_requests')
        
        if (user_role == 'SUPPORT' and ticket.type == Ticket.Type.BOOKING_SUPPORT):
            messages.error(request, "Bạn không có quyền xem các yêu cầu Hỗ trợ Đặt phòng.")
            return redirect('manage_requests')

    responses = ticket.responses.select_related('responder').order_by('created_at')
    
    # Logic xác định URL quay lại
    if ticket.type == Ticket.Type.COMPLAINT:
        back_url = reverse('manage_complaints')
        header_title = 'Chi tiết Khiếu nại'
        # Chỉ CSKH mới thấy danh sách nhân viên để gán
        if user_role == 'SUPPORT' or user_role == 'ADMIN':
             staff_members = CustomUser.objects.filter(role='SUPPORT', is_active=True)
        else:
             staff_members = None
    else:
        back_url = reverse('manage_requests')
        header_title = 'Chi tiết Yêu cầu'
        staff_members = None

    # Khởi tạo form
    response_form = TicketResponseForm()
    resolution_form = ComplaintResolutionForm(instance=ticket)
    
    if request.method == 'POST':
        # 1. XỬ LÝ GỬI PHẢN HỒI (CHAT)
        if 'submit_response' in request.POST:
            response_form = TicketResponseForm(request.POST)
            if response_form.is_valid():
                response = response_form.save(commit=False)
                response.ticket = ticket
                response.responder = request.user
                response.save()
                
                # Cập nhật trạng thái
                if ticket.status == Ticket.Status.NEW:
                    ticket.status = Ticket.Status.IN_PROGRESS
                
                ticket.save()
                messages.success(request, "Đã gửi phản hồi thành công.")
                return redirect('ticket_detail', pk=ticket.pk)

        # 2. XỬ LÝ LƯU KẾT QUẢ/ĐÓNG TICKET (CHO KHIẾU NẠI)
        elif 'submit_resolution' in request.POST:
            resolution_form = ComplaintResolutionForm(request.POST, instance=ticket)
            if resolution_form.is_valid():
                resolution_form.save()
                ticket.status = Ticket.Status.RESOLVED # Đóng ticket
                ticket.save()
                messages.success(request, "Đã lưu kết quả xử lý và đóng Khiếu nại.")
                return redirect('ticket_detail', pk=ticket.pk)

    context = {
        'ticket': ticket,
        'responses': responses,
        'form': response_form,
        'resolution_form': resolution_form,
        'header_title': header_title,
        'back_url': back_url,
        'staff_members': staff_members, # Gửi danh sách CSKH (chỉ cho Khiếu nại)
    }
    return render(request, 'crm/dashboard_ticket_detail.html', context)

@user_passes_test(is_crm_staff)
def resolve_ticket_view(request, pk):
    """
    View để nhân viên đánh dấu một ticket là đã hoàn thành.
    """
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, pk=pk)
        
        if ticket.type != Ticket.Type.COMPLAINT:
            ticket.status = Ticket.Status.RESOLVED
            ticket.save()
            short_ticket_id = str(ticket.ticket_id)[:8]
            messages.success(request, f"Đã đóng thành công yêu cầu #{short_ticket_id}...")
        else:
            messages.error(request, "Khiếu nại phải được đóng bằng cách 'Lưu Kết quả Xử lý'.")
            
    return redirect('ticket_detail', pk=pk)

@login_required
def complaint_submission_view(request):
    """
    Xử lý trang gửi Khiếu nại, chỉ dành cho người dùng đã đăng nhập.
    - Xử lý phương thức POST để tạo Ticket loại 'COMPLAINT'.
    - ModelForm sẽ tự động xử lý file đính kèm.
    """
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            # Tạo ticket nhưng chưa lưu vào DB để gán thêm thông tin
            ticket = form.save(commit=False)
            ticket.customer = request.user
            ticket.type = Ticket.Type.COMPLAINT
            ticket.status = Ticket.Status.NEW
            ticket.save() # Lưu ticket vào DB

            return JsonResponse({
                'success': True,
                'home_url': reverse('homepage'),
                'success_url_list': reverse('my_complaints')
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

            return render(request, 'crm/submit_complaint.html', context)
    else:
        form = ComplaintForm()

    context = {
        'form': form,
    }
    return render(request, 'crm/submit_complaint.html', context)

@user_passes_test(is_admin)
def assign_ticket_view(request, pk):
    """
    Xử lý việc gán một ticket cho một nhân viên.
    """
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, pk=pk)
        
        # Chỉ cho phép gán Khiếu nại
        if ticket.type != Ticket.Type.COMPLAINT:
            messages.error(request, "Chỉ có thể phân công Khiếu nại. Yêu cầu tư vấn được định tuyến tự động.")
            return redirect(request.META.get('HTTP_REFERER', 'manage_requests'))
            
        staff_id = request.POST.get('staff_member')
        
        if staff_id:
            # Đảm bảo chỉ gán cho CSKH
            staff_member = get_object_or_404(CustomUser, pk=staff_id, role='SUPPORT') 
            ticket.assigned_to = staff_member
            ticket.status = Ticket.Status.IN_PROGRESS # Tự động chuyển trạng thái
            ticket.save()
            messages.success(request, f"Đã gán khiếu nại #{ticket.id} cho nhân viên {staff_member.username}.")
        else:
            ticket.assigned_to = None
            ticket.save()
            messages.info(request, f"Đã bỏ gán nhân viên cho khiếu nại #{ticket.id}.")

    return redirect(request.META.get('HTTP_REFERER', 'manage_complaints'))

def zalo_support_view(request):
    """
    Hiển thị trang thông tin hỗ trợ qua Zalo.
    """
    return render(request, 'crm/zalo_support.html')
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import OuterRef, Subquery
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import ConsultationRequestForm, TicketResponseForm, CustomerResponseForm, ComplaintForm
from .models import Ticket, TicketResponse

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
    success = False

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
            
            # Đặt tín hiệu thành công là True
            success = True
            # Tạo một form mới, trống để hiển thị lại trên trang
            form = ConsultationRequestForm() 
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
        'success': success # Gửi tín hiệu thành công sang template
    }
    return render(request, 'crm/consultation_request.html', context)

@login_required
def my_tickets_view(request):
    """
    Hiển thị danh sách các yêu cầu của khách hàng.
    Nâng cấp: Lấy thêm thông tin về phản hồi cuối cùng cho mỗi yêu cầu.
    """
    # Tạo một subquery để lấy tin nhắn của phản hồi mới nhất
    latest_response_message = TicketResponse.objects.filter(
        ticket=OuterRef('pk')
    ).order_by('-created_at').values('message')[:1]

    # Tạo một subquery để lấy tên người phản hồi mới nhất
    latest_responder_name = TicketResponse.objects.filter(
        ticket=OuterRef('pk')
    ).order_by('-created_at').values('responder__full_name')[:1]

    # Truy vấn chính: Lấy tất cả ticket của user và đính kèm thông tin từ subquery
    tickets = Ticket.objects.filter(customer=request.user).annotate(
        last_response_message=Subquery(latest_response_message),
        last_responder_name=Subquery(latest_responder_name)
    ).order_by('-created_at')

    context = {
        'tickets': tickets
    }
    return render(request, 'crm/my_tickets.html', context)

@login_required
def customer_ticket_detail_view(request, pk):
    """
    Hiển thị chi tiết một yêu cầu và cho phép khách hàng gửi phản hồi.
    """    
    ticket = get_object_or_404(Ticket, pk=pk, customer=request.user) # Đảm bảo khách chỉ xem được ticket của mình
    responses = ticket.responses.select_related('responder').order_by('created_at')
    context = {
        'ticket': ticket,
        'responses': responses
    }
    return render(request, 'crm/customer_ticket_detail.html', context)

# ==============================================================================
# VIEWS DÀNH CHO NHÂN VIÊN (DASHBOARD)
# ==============================================================================

def is_crm_staff(user):
    """Hàm kiểm tra quyền, trả về True nếu user là CSKH hoặc Admin."""
    return user.is_authenticated and (user.role in ['CRM_STAFF', 'ADMIN'])

@user_passes_test(is_crm_staff)
def manage_requests_view(request):
    """
    Hiển thị trang quản lý các yêu cầu (KHÔNG bao gồm Khiếu nại).
    """
    status_filter = request.GET.get('status')
    
    # Lọc ra tất cả ticket KHÔNG PHẢI là khiếu nại
    tickets = Ticket.objects.exclude(type=Ticket.Type.COMPLAINT).select_related('customer').order_by('-created_at')

    if status_filter in Ticket.Status.values:
        tickets = tickets.filter(status=status_filter)

    context = {
        'tickets': tickets,
        'current_filter': status_filter,
        'ticket_statuses': Ticket.Status.choices,
        'header_title': 'Quản lý Yêu cầu', # Tiêu đề động cho template
        'back_url_to_dashboard': True # Tín hiệu để link quay lại trỏ về dashboard chính
    }
    return render(request, 'crm/dashboard_tickets.html', context)

@user_passes_test(is_crm_staff)
def manage_complaints_view(request):
    """
    Hiển thị trang quản lý chỉ các KHIẾU NẠI.
    """
    status_filter = request.GET.get('status')

    # Chỉ lọc ra các ticket là KHIẾU NẠI
    tickets = Ticket.objects.filter(type=Ticket.Type.COMPLAINT).select_related('customer').order_by('-created_at')

    if status_filter in Ticket.Status.values:
        tickets = tickets.filter(status=status_filter)

    context = {
        'tickets': tickets,
        'current_filter': status_filter,
        'ticket_statuses': Ticket.Status.choices,
        'header_title': 'Quản lý Khiếu nại', # Tiêu đề động cho template
        'back_url_to_dashboard': True # Tín hiệu để link quay lại trỏ về dashboard chính
    }
    return render(request, 'crm/dashboard_tickets.html', context)

@user_passes_test(is_crm_staff)
def ticket_detail_view(request, pk):
    """
    Hiển thị chi tiết một yêu cầu và xử lý phản hồi.
    Nâng cấp: Tự động xác định URL để quay lại danh sách tương ứng.
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    responses = ticket.responses.select_related('responder').order_by('created_at')
    
    # Logic xác định URL quay lại
    if ticket.type == Ticket.Type.COMPLAINT:
        back_url = reverse('manage_complaints')
        header_title = 'Chi tiết Khiếu nại'
    else:
        back_url = reverse('manage_requests')
        header_title = 'Chi tiết Yêu cầu'
    
    if request.method == 'POST':
        # ... (phần xử lý POST giữ nguyên không đổi)
        form = TicketResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.ticket = ticket
            response.responder = request.user
            response.save()
            ticket.status = Ticket.Status.IN_PROGRESS
            ticket.save()
            messages.success(request, "Đã gửi phản hồi thành công.")
            return redirect('ticket_detail', pk=ticket.pk)
    else:
        form = TicketResponseForm()

    context = {
        'ticket': ticket,
        'responses': responses,
        'form': form,
        'header_title': header_title, # Gửi tiêu đề động
        'back_url': back_url,      # Gửi URL quay lại động
    }
    return render(request, 'crm/dashboard_ticket_detail.html', context)

@login_required
def customer_ticket_detail_view(request, pk):
    """
    Hiển thị chi tiết một yêu cầu cho khách hàng và xử lý việc họ gửi trả lời.
    """
    ticket = get_object_or_404(Ticket, pk=pk, customer=request.user)
    responses = ticket.responses.select_related('responder').order_by('created_at')

    # Xử lý khi khách hàng gửi form trả lời
    if request.method == 'POST':
        form = CustomerResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.ticket = ticket
            response.responder = request.user # Người trả lời là khách hàng đang đăng nhập
            response.save()
            
            # CẬP NHẬT TRẠNG THÁI TICKET: Chuyển lại thành "Mới" để nhân viên chú ý
            ticket.status = Ticket.Status.AWAITING_STAFF_RESPONSE            
            ticket.save()
            
            messages.success(request, "Đã gửi trả lời thành công.")
            # Tải lại chính trang này để xem tin nhắn mới
            return redirect('customer_ticket_detail', pk=ticket.pk)
    else:
        # Khi mới vào trang, tạo một form trống
        form = CustomerResponseForm()

    context = {
        'ticket': ticket,
        'responses': responses,
        'form': form # Gửi form sang template
    }
    return render(request, 'crm/customer_ticket_detail.html', context)

@user_passes_test(is_crm_staff)
def resolve_ticket_view(request, pk):
    """View để nhân viên đánh dấu một ticket là đã hoàn thành."""
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, pk=pk)
        ticket.status = Ticket.Status.RESOLVED
        ticket.save()
        short_ticket_id = str(ticket.ticket_id)[:8]
        messages.success(request, f"Đã đóng thành công yêu cầu #{short_ticket_id}...")    
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

            # Xử lý các file đính kèm
            files = request.FILES.getlist('attachments')
            for f in files:
                TicketAttachment.objects.create(ticket=ticket, file=f)
            
            messages.success(request, "Gửi khiếu nại thành công! Chúng tôi sẽ xem xét và phản hồi sớm nhất.")
            return redirect('my_tickets') # Chuyển hướng về trang danh sách yêu cầu
    else:
        form = ComplaintForm()

    context = {
        'form': form
    }
    return render(request, 'crm/submit_complaint.html', context)
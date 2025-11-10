from django import forms
from captcha.fields import CaptchaField
from .models import TicketResponse, Ticket
from django.forms.widgets import ClearableFileInput


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


class ConsultationRequestForm(forms.Form):
    """
    Form cho phép khách hàng gửi yêu cầu tư vấn.
    """
    REQUEST_TYPE_CHOICES = [
        ('CONSULTATION', 'Tư vấn Dịch vụ'),
        ('BOOKING_SUPPORT', 'Hỗ trợ Đặt phòng'),
        ('OTHER', 'Yêu cầu Khác'),
    ]

    full_name = forms.CharField(
        label="Họ và Tên",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập họ và tên của bạn'
        })
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@gmail.com'
        })
    )
    phone_number = forms.CharField(
        label="Số điện thoại",
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0123456789'
        })
    )
    request_type = forms.ChoiceField(
        label="Loại yêu cầu",
        choices=REQUEST_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    content = forms.CharField(
        label="Nội dung",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Nhập chi tiết yêu cầu của bạn...'
        })
    )
    captcha = CaptchaField(label="Mã xác thực")


class ComplaintForm(forms.ModelForm):
    """
    Form cho phép khách hàng đã đăng nhập gửi khiếu nại.
    """
    class Meta:
        model = Ticket
        fields = ['subject', 'complaint_type', 'incident_time', 'description', 'attachment']
        labels = {
            'subject': 'Tiêu đề Khiếu nại',
            'complaint_type': 'Phân loại khiếu nại',
            'incident_time': 'Thời gian xảy ra vụ việc',
            'description': 'Nội dung chi tiết',
            'attachment': 'Đính kèm một tệp (nếu có)',
        }
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ví dụ: Phòng không sạch sẽ, thái độ nhân viên...'
            }),
            'complaint_type': forms.Select(attrs={'class': 'form-control'}),
            'incident_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Vui lòng mô tả chi tiết vấn đề bạn gặp phải...'
            }),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class TicketEditForm(forms.ModelForm):
    """Form cho phép khách hàng sửa nội dung yêu cầu tư vấn."""
    class Meta:
        model = Ticket
        fields = ['description'] # Chỉ cho phép sửa trường nội dung
        labels = {
            'description': 'Nội dung yêu cầu mới'
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
        }
        
class TicketResponseForm(forms.ModelForm):
    """
    Form để nhân viên CSKH nhập nội dung phản hồi.
    """
    class Meta:
        model = TicketResponse
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Nhập nội dung phản hồi tại đây...',
                'class': 'form-control'
            }),
        }
        labels = {
            'message': 'Nội dung phản hồi'
        }

class CustomerResponseForm(forms.ModelForm):
    """
    Form đơn giản để khách hàng nhập nội dung trả lời.
    """
    class Meta:
        model = TicketResponse
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Nhập nội dung trả lời của bạn tại đây...',
                'class': 'form-control'
            }),
        }
        labels = {
            'message': 'Nội dung trả lời của bạn'
        }

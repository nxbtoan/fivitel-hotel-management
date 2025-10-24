from django import forms
from django.utils import timezone
from services.models import Service
from .models import RoomClass, Booking, PaymentProof
# from django_countries import countries
from django_countries.fields import CountryField

class ServiceCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """
    Widget tùy chỉnh để tự động thêm thuộc tính `data-price` và `price`
    vào mỗi lựa chọn khi render.
    """
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        # Gọi phương thức gốc để lấy các thuộc tính mặc định
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        
        # 'value' ở đây trỏ đến đối tượng Service
        if value and hasattr(value, 'instance') and hasattr(value.instance, 'price'):
            # 1. Thêm thuộc tính data-price vào thẻ input
            option['attrs']['data-price'] = value.instance.price
            
            # 2. (QUAN TRỌNG) Gói giá tiền vào chính đối tượng 'option'
            # để template có thể truy cập trực tiếp
            option['price'] = value.instance.price
        
        return option

class BookingOptionsForm(forms.Form):
    """
    Form cho Trang Tùy chọn: Khách hàng chọn ngày, số khách và dịch vụ đi kèm.
    """
    check_in_date = forms.DateField(
        label="Ngày nhận phòng",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    check_out_date = forms.DateField(
        label="Ngày trả phòng",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    adults = forms.IntegerField(label="Người lớn", min_value=1, initial=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    children = forms.IntegerField(label="Trẻ em", min_value=0, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
    additional_services = forms.ModelMultipleChoiceField(
        label="Dịch vụ đi kèm",
        queryset=Service.objects.all(),

        widget=ServiceCheckboxSelectMultiple,
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get("check_in_date")
        check_out = cleaned_data.get("check_out_date")
        if check_in and check_out:
            if check_in < timezone.now().date():
                self.add_error('check_in_date', "Ngày nhận phòng không thể là ngày trong quá khứ.")
            if check_out <= check_in:
                self.add_error('check_out_date', "Ngày trả phòng phải sau ngày nhận phòng.")
        return cleaned_data
    
class CheckoutForm(forms.Form):
    """
    Form thu thập thông tin khách hàng ở bước cuối cùng trước khi đặt phòng.
    """
    # --- Định nghĩa các lựa chọn ---
    BOOKING_FOR_CHOICES = [
        ('SELF', 'Cho tôi'),
        ('SOMEONE_ELSE', 'Cho người khác'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('BANK_TRANSFER', 'Chuyển khoản Ngân hàng'),
        ('PAY_LATER', 'Thanh toán tại quầy'),
    ]

    # --- Định nghĩa các trường ---
    booking_for = forms.ChoiceField(
        choices=BOOKING_FOR_CHOICES,
        widget=forms.RadioSelect,
        initial='SELF',
        required=False
    )
    full_name = forms.CharField(label="Họ và tên khách ở chính", max_length=100)
    email = forms.EmailField(label="Email liên hệ")
    phone_number = forms.CharField(label="Số điện thoại", max_length=20)
    nationality = CountryField().formfield(label="Quốc tịch")
    special_requests = forms.CharField(
        label="Yêu cầu đặc biệt (nếu có)",
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect,
        initial='BANK_TRANSFER',
        required=True
    )

    # --- PHẦN QUAN TRỌNG NHẤT ĐỂ THÊM CLASS CSS ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tự động thêm class 'form-control' cho các trường input, select, textarea
        self.fields['full_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['phone_number'].widget.attrs.update({'class': 'form-control'})
        self.fields['nationality'].widget.attrs.update({'class': 'form-control'})
        self.fields['special_requests'].widget.attrs.update({'class': 'form-control'})

class BookingEditForm(forms.ModelForm):
    """
    Form chuyên dụng cho phép khách hàng chỉnh sửa thông tin
    người nhận phòng và các dịch vụ đi kèm của một đơn hàng đã có.
    """
    class Meta:
        model = Booking
        # Chỉ định các trường được phép chỉnh sửa
        fields = ['guest_full_name', 'guest_email', 'guest_phone_number', 'additional_services']
        labels = {
            'guest_full_name': 'Họ tên người nhận phòng',
            'guest_email': 'Email người nhận phòng',
            'guest_phone_number': 'Số điện thoại người nhận phòng',
            'additional_services': 'Cập nhật các dịch vụ đi kèm',
        }
        # Dùng CheckboxSelectMultiple để có giao diện chọn dịch vụ tốt hơn
        widgets = {
            'additional_services': forms.CheckboxSelectMultiple,
        }

class PaymentProofForm(forms.ModelForm):
    """
    Form để khách hàng tải lên ảnh bằng chứng đã chuyển khoản.
    """
    class Meta:
        model = PaymentProof
        fields = ['image']
        labels = {
            'image': 'Chọn ảnh bằng chứng thanh toán'
        }


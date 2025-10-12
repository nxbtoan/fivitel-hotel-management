from django import forms
from django.utils import timezone
from services.models import Service
from .models import RoomClass, Booking, PaymentProof
from django_countries import countries

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
    Form cho Nhập thông tin khách hàng: Khách hàng điền thông tin cá nhân để hoàn tất đặt phòng.
    """
    # Lựa chọn đặt cho ai, dùng để điều khiển bằng JS
    booking_for = forms.ChoiceField(
        label="Thông tin của khách ở chính:",
        choices=(('myself', 'Cho tôi'), ('other', 'Cho người khác')),
        widget=forms.RadioSelect,
        initial='myself'
    )
    
    # Các trường thông tin cá nhân
    full_name = forms.CharField(label="Họ và Tên")
    email = forms.EmailField(label="Email")
    phone_number = forms.CharField(label="Số điện thoại")
    nationality = forms.ChoiceField(
        label="Quốc tịch",
        choices=countries
    )
    payment_method = forms.ChoiceField(
        label="Chọn phương thức thanh toán",
        choices=Booking.PaymentMethod.choices,
        widget=forms.RadioSelect,
        initial=Booking.PaymentMethod.PAY_LATER
    )
    special_requests = forms.CharField(
        label="Yêu cầu cá nhân",
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Nếu có bất kỳ nhu cầu đặc biệt nào, xin vui lòng chia sẻ với chúng tôi.'})
    )

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
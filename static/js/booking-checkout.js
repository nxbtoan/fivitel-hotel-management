document.addEventListener('DOMContentLoaded', function() {
    const checkoutForm = document.getElementById('checkoutForm');
    if (!checkoutForm) return;

    // Lấy các element form
    const bookingForRadios = document.querySelectorAll('input[name="booking_for"]');
    const nameInput = document.querySelector('input[name="full_name"]');
    const emailInput = document.querySelector('input[name="email"]');
    const phoneInput = document.querySelector('input[name="phone_number"]');
    const nationalitySelect = document.querySelector('select[name="nationality"]');

    // Đọc thông tin người dùng từ data attributes
    const userInfo = {
        fullName: checkoutForm.dataset.fullName,
        email: checkoutForm.dataset.email,
        phone: checkoutForm.dataset.phone,
        nationality: checkoutForm.dataset.nationality
    };

    function toggleGuestDetails(value) {
        // TRƯỜG HỢP 1: Chọn "Cho người khác"
        if (value === 'SOMEONE_ELSE') {
            nameInput.value = '';
            emailInput.value = '';
            phoneInput.value = '';
            if (nationalitySelect) {
                nationalitySelect.value = '';
            }

            nameInput.readOnly = false;
            emailInput.readOnly = false;
            phoneInput.readOnly = false;

        } else {
            nameInput.value = userInfo.fullName;
            emailInput.value = userInfo.email;
            phoneInput.value = userInfo.phone;
            if (nationalitySelect && userInfo.nationality) {
                nationalitySelect.value = userInfo.nationality;
            }

            nameInput.readOnly = true;
            emailInput.readOnly = true;
            phoneInput.readOnly = true;
        }
    }

    // Gắn sự kiện 'change' cho các nút radio
    bookingForRadios.forEach(radio => {
        // Chạy lần đầu khi tải trang cho nút được check sẵn
        if (radio.checked) {
            toggleGuestDetails(radio.value);
        }
        // Gắn sự kiện cho những lần thay đổi sau
        radio.addEventListener('change', function() {
            toggleGuestDetails(this.value);
        });
    });

    // Phần code xử lý giao diện payment option của bạn vẫn rất tốt và được giữ nguyên
    const paymentOptions = document.querySelectorAll('.payment-option-card');
    
    paymentOptions.forEach(option => {
        option.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            if(radio) {
                radio.checked = true;
            }
        });
    });
});
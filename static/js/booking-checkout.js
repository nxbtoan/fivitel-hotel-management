document.addEventListener('DOMContentLoaded', function() {
    const checkoutForm = document.getElementById('checkoutForm');
    if (!checkoutForm) return;

    // Lấy các element form
    const bookingForRadios = document.querySelectorAll('input[name="booking_for"]');
    const guestDetails = document.getElementById('guest-details');
    const nameInput = document.querySelector('input[name="full_name"]');
    const emailInput = document.querySelector('input[name="email"]');
    const phoneInput = document.querySelector('input[name="phone_number"]');
    const nationalitySelect = document.querySelector('select[name="nationality"]')

    // Đọc thông tin người dùng từ data attributes
    const userInfo = {
        isAuthenticated: checkoutForm.dataset.isAuthenticated === 'true',
        fullName: checkoutForm.dataset.fullName,
        email: checkoutForm.dataset.email,
        phone: checkoutForm.dataset.phone,
        nationality: checkoutForm.dataset.nationality
    };

    function toggleGuestDetails(value) {
        // TRƯỜG HỢP 1: Chọn "Cho người khác"
        if (value === 'other') {
            // Luôn hiển thị form
            guestDetails.style.display = 'grid';
            // Luôn xóa trắng các ô để người dùng nhập mới
            nameInput.value = '';
            emailInput.value = '';
            phoneInput.value = '';
            if (nationalitySelect) nationalitySelect.value = '';
        } 
        // TRƯỜNG HỢP 2: Chọn "Cho tôi"
        else { // value === 'myself'
            // Nếu người dùng đã đăng nhập
            if (userInfo.isAuthenticated) {
                // Điền lại thông tin của họ và ẩn form đi
                nameInput.value = userInfo.fullName;
                emailInput.value = userInfo.email;
                phoneInput.value = userInfo.phone;
                if (nationalitySelect) nationalitySelect.value = userInfo.nationality;
            } 
            // Nếu người dùng chưa đăng nhập (khách vãng lai đặt cho chính họ)
            else {
                // Vẫn hiển thị form và đảm bảo nó trống để họ tự điền
                guestDetails.style.display = 'grid';
                nameInput.value = '';
                emailInput.value = '';
                phoneInput.value = '';
                if (nationalitySelect) nationalitySelect.value = '';
            }
        }
    }

    // Chạy hàm lần đầu khi tải trang
    const initialChoice = document.querySelector('input[name="booking_for"]:checked').value;
    toggleGuestDetails(initialChoice);

    // Gắn sự kiện 'change' cho các nút radio
    bookingForRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            toggleGuestDetails(this.value);
        });
    });

    const paymentOptions = document.querySelectorAll('.payment-option');
    const paymentRadios = document.querySelectorAll('input[name="payment_method"]');

    // Cập nhật viền khi radio thay đổi
    function updatePaymentSelection() {
        paymentRadios.forEach(radio => {
            const parent = radio.closest('.payment-option');
            if (radio.checked) {
                parent.style.borderColor = '#0A378C';
            } else {
                parent.style.borderColor = '#ddd';
            }
        });
    }

    // Gắn sự kiện click cho cả khối div
    paymentOptions.forEach(option => {
        option.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            radio.checked = true;
            updatePaymentSelection();
        });
    });

    // Chạy lần đầu
    updatePaymentSelection();


});
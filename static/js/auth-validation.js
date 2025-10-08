document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.getElementById('id_password1');
    const passwordMsg = document.getElementById('password-validation-msg');
    const submitBtn = document.getElementById('submit-btn');

    if (passwordInput) { // Chỉ chạy code nếu tìm thấy ô mật khẩu
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const hasLength = password.length >= 8;
            // Biểu thức chính quy (regex) để tìm ký tự đặc biệt
            const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

            let isValid = hasLength && hasSpecialChar;

            if (password.length === 0) {
                passwordMsg.textContent = 'Mật khẩu tối thiểu 8 ký tự, có ít nhất 1 ký tự đặc biệt.';
                passwordMsg.style.color = '#6c757d'; // Màu helptext mặc định
            } else if (isValid) {
                passwordMsg.textContent = 'Mật khẩu hợp lệ!';
                passwordMsg.style.color = 'green';
            } else {
                let errorMsg = 'Mật khẩu cần: ';
                if (!hasLength) {
                    errorMsg += 'ít nhất 8 ký tự';
                }
                if (!hasLength && !hasSpecialChar) {
                    errorMsg += ', ';
                }
                if (!hasSpecialChar) {
                    errorMsg += 'ít nhất 1 ký tự đặc biệt';
                }
                errorMsg += '.';
                passwordMsg.textContent = errorMsg;
                passwordMsg.style.color = '#dc3545'; // Màu đỏ lỗi
            }
        });
    }
});
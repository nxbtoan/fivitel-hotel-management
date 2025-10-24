document.addEventListener('DOMContentLoaded', function() {
    // Lấy các element form
    const checkInInput = document.getElementById('id_check_in_date');
    const checkOutInput = document.getElementById('id_check_out_date');
    const servicesCheckboxes = document.querySelectorAll('input[name="additional_services"]');
    
    // Lấy các element trong sidebar
    const summaryBasePrice = document.getElementById('summary-base-price');
    const summaryNights = document.getElementById('summary-nights');
    const summaryRoomTotal = document.getElementById('summary-room-total');
    const summaryServicesTotal = document.getElementById('summary-services-total');
    const summaryGrandTotal = document.getElementById('summary-grand-total');
    const sidebar = document.querySelector('.summary-sidebar');
    const basePrice = parseFloat(sidebar.dataset.basePrice);

    // TỰ ĐỘNG ĐIỀN GIÁ DỊCH VỤ KHI TẢI TRANG
    const formatter = new Intl.NumberFormat('vi-VN');
    servicesCheckboxes.forEach(checkbox => {
        const price = parseFloat(checkbox.dataset.price || 0);
        const wrapper = checkbox.closest('.choice-wrapper');
        if (wrapper) {
            const span = wrapper.querySelector('.choice-price');
            if (span) {
                // Điền giá đã được định dạng vào
                span.textContent = `+ ${formatter.format(price)} VNĐ`;
            }
        }
    });

    //-----------------------------------------------------------
    function calculateTotal() {
        // 1. Tính tiền phòng
        let roomTotal = 0;
        let nights = 0;
        const checkInDate = new Date(checkInInput.value);
        const checkOutDate = new Date(checkOutInput.value);
        if (checkInInput.value && checkOutInput.value && checkOutDate > checkInDate) {
            const timeDiff = checkOutDate.getTime() - checkInDate.getTime();
            nights = Math.ceil(timeDiff / (1000 * 3600 * 24));
            roomTotal = nights * basePrice;
        }

        // 2. Tính tiền dịch vụ
        let servicesTotal = 0;
        servicesCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                servicesTotal += parseFloat(checkbox.dataset.price || 0);
            }
        });

        // 3. Tính tổng cộng
        const grandTotal = roomTotal + servicesTotal;

        // 4. Cập nhật giao diện sidebar
        summaryBasePrice.textContent = formatter.format(basePrice);
        summaryNights.textContent = nights;
        summaryRoomTotal.textContent = formatter.format(roomTotal);
        summaryServicesTotal.textContent = formatter.format(servicesTotal);
        summaryGrandTotal.textContent = formatter.format(grandTotal);
    }

    // Gắn sự kiện 'change' cho tất cả các input
    checkInInput.addEventListener('change', calculateTotal);
    checkOutInput.addEventListener('change', calculateTotal);
    servicesCheckboxes.forEach(checkbox => checkbox.addEventListener('change', calculateTotal));

    // Chạy lần đầu khi tải trang
    calculateTotal();
});
document.addEventListener('DOMContentLoaded', function() {
    // --- Logic cho Pop-up Xóa ---
    const deleteModal = document.getElementById('delete-confirmation-modal');
    const deleteForm = document.getElementById('delete-form');
    const closeBtn = document.querySelector('.close-modal-btn');
    const cancelBtn = document.getElementById('cancel-delete-btn');
    const deleteButtons = document.querySelectorAll('.open-delete-modal');

    // Mở pop-up
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Lấy URL xóa từ data attribute của nút bấm
            const deleteUrl = this.dataset.deleteUrl;
            // Gán URL này vào action của form trong pop-up
            deleteForm.action = deleteUrl;
            // Hiển thị pop-up
            deleteModal.style.display = 'flex';
        });
    });

    // Hàm để đóng pop-up
    function closeModal() {
        deleteModal.style.display = 'none';
    }

    // Gắn sự kiện đóng cho các nút
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

    // Đóng pop-up khi click ra ngoài
    window.addEventListener('click', function(event) {
        if (event.target == deleteModal) {
            closeModal();
        }
    });
});
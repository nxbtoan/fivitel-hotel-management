document.addEventListener('DOMContentLoaded', function() {
    // --- LOGIC CHO DROPDOWN MENU ---
    const userMenuTrigger = document.getElementById('user-menu-trigger');
    const dropdownMenu = document.getElementById('dropdown-menu');

    if (userMenuTrigger && dropdownMenu) {
        userMenuTrigger.addEventListener('click', function(event) {
            event.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });
    }

    window.addEventListener('click', function(event) {
        if (dropdownMenu && userMenuTrigger && !dropdownMenu.contains(event.target) && !userMenuTrigger.contains(event.target)) {
            dropdownMenu.classList.remove('show');
        }
    });

    // --- LOGIC CHO LIGHTBOX CỦA THƯ VIỆN ẢNH ---
    const galleryImages = document.querySelectorAll('.gallery-item img');
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    const closeBtn = document.querySelector('.lightbox-close');

    // Kiểm tra xem các thành phần HTML có tồn tại không
    if (!lightbox || !lightboxImg || !closeBtn) {
        console.error("LỖI: Không tìm thấy các thành phần HTML của Lightbox (#lightbox, #lightbox-img, .lightbox-close). Hãy kiểm tra lại file base.html.");
        return; // Dừng script nếu thiếu HTML
    }
    
    // Gắn sự kiện click cho từng ảnh
    galleryImages.forEach((img, index) => {        
        img.addEventListener('click', function() {
            lightboxImg.src = this.src;
            lightbox.classList.add('show');
        });
    });
    
    // Logic để đóng lightbox
    const closeLightbox = () => {
        lightbox.classList.remove('show');
    };

    closeBtn.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) {
            closeLightbox();
        }
    });
});
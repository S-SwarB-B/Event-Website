// event-form.js
document.addEventListener('DOMContentLoaded', function() {
    // Предпросмотр изображения
    const imageInput = document.querySelector('input[type="file"]');
    const imagePreview = document.getElementById('imagePreview');

    if (imageInput && imagePreview) {
        const previewImg = imagePreview.querySelector('img');

        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    imagePreview.classList.add('active');
                };
                reader.readAsDataURL(file);
            } else {
                imagePreview.classList.remove('active');
            }
        });
    }

    // Минимальная дата (сегодня)
    const dateInput = document.querySelector('input[type="date"]');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('min', today);
    }
});
// toast.js - Уведомления
document.addEventListener('DOMContentLoaded', function() {
    const toasts = document.querySelectorAll('.toast');

    toasts.forEach((toast, index) => {
        // Добавляем задержку для последовательного появления
        toast.style.animationDelay = `${index * 0.1}s`;

        // Автоматическое скрытие через 4 секунды
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, 300);
            }
        }, 4000 + (index * 500));

        // Закрытие по клику
        toast.addEventListener('click', function() {
            this.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                if (this.parentNode) {
                    this.remove();
                }
            }, 300);
        });

        // Добавляем кнопку закрытия
        const closeBtn = document.createElement('span');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = `
            margin-left: auto;
            font-size: 20px;
            cursor: pointer;
            opacity: 0.7;
            transition: opacity 0.2s;
        `;
        closeBtn.addEventListener('mouseenter', () => closeBtn.style.opacity = '1');
        closeBtn.addEventListener('mouseleave', () => closeBtn.style.opacity = '0.7');
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        });
        toast.appendChild(closeBtn);
    });
});
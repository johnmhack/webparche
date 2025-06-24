// Encapsulamos todo el código para evitar variables globales
(function() {
    document.addEventListener('DOMContentLoaded', () => {
        // Swiper para testimonios
        const swiper = new Swiper('.swiper', {
            slidesPerView: 'auto',
            spaceBetween: 30,
            loop: true,
            allowTouchMove: false,
            speed: 6000,
            autoplay: {
                delay: 0,
                disableOnInteraction: false,
            },
        });

        const swiperContainer = document.querySelector('.swiper');
        swiperContainer.addEventListener('mouseenter', () => {
            swiper.autoplay.stop();
        });
        swiperContainer.addEventListener('mouseleave', () => {
            swiper.autoplay.start();
        });

        // Preguntas frecuentes (FAQ)
        document.querySelectorAll('.faq-item h6').forEach(faqItemHeading => {
            faqItemHeading.addEventListener('click', () => {
                const faqItem = faqItemHeading.parentElement;
                // Cierra todos los demás items antes de abrir el actual
                document.querySelectorAll('.faq-item').forEach(item => {
                    if (item !== faqItem && item.classList.contains('active')) {
                        item.classList.remove('active');
                        item.querySelector('p').style.maxHeight = null;
                    }
                });
                // Alterna el estado activo del item clickeado
                faqItem.classList.toggle('active');
                const answer = faqItem.querySelector('p');
                if (faqItem.classList.contains('active')) {
                    answer.style.maxHeight = answer.scrollHeight + "px";
                } else {
                    answer.style.maxHeight = null;
                }
            });
        });

        // Menú hamburguesa
        const menuIcon = document.querySelector('.menu-icon');
        const menu = document.querySelector('.menu');
        if (!menuIcon || !menu) {
            console.error('Error: No se encuentran los elementos .menu-icon o .menu en el DOM.');
            return;
        }
        menuIcon.addEventListener('click', () => {
            const isActive = menu.classList.toggle('active');
            menuIcon.setAttribute('aria-expanded', isActive);
        });
    });

    // Navbar auto-hide al hacer scroll
    let lastScrollY = window.scrollY;
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', () => {
        if (!navbar) return;
        if (window.scrollY > lastScrollY && window.scrollY > 60) {
            // Scroll hacia abajo, ocultar navbar
            navbar.classList.add('navbar--hidden');
        } else {
            // Scroll hacia arriba, mostrar navbar
            navbar.classList.remove('navbar--hidden');
        }
        lastScrollY = window.scrollY;
    });
})();







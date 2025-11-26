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

        // Menú hamburguesa mejorado
    const menuIcon = document.querySelector('.menu-icon');
    const menu = document.querySelector('.menu');
    const menuContainer = document.querySelector('.navbar__menu-container');
    if (!menuIcon || !menu) {
        // Error: No se encuentran los elementos .menu-icon o .menu en el DOM.
        return;
    }
    
    // Función para cerrar menú
    function closeMenu() {
        menu.classList.remove('active');
        menuIcon.classList.remove('active');
        if (menuContainer) menuContainer.classList.remove('active');
        menuIcon.setAttribute('aria-expanded', 'false');
    }
    
    // Función para abrir menú
    function openMenu() {
        menu.classList.add('active');
        menuIcon.classList.add('active');
        if (menuContainer) menuContainer.classList.add('active');
        menuIcon.setAttribute('aria-expanded', 'true');
    }
    
    // Toggle del menú hamburguesa
    menuIcon.addEventListener('click', (e) => {
        e.preventDefault();
        const isActive = menu.classList.contains('active');
        
        if (isActive) {
            closeMenu();
        } else {
            openMenu();
        }
    });

    // Cerrar menú al hacer clic en un enlace
    const menuLinks = document.querySelectorAll('.menu li a');
    menuLinks.forEach(link => {
        link.addEventListener('click', () => {
            closeMenu();
        });
    });
    
    // Cerrar menú al hacer clic fuera de él
    document.addEventListener('click', (e) => {
        if (!menu.contains(e.target) && !menuIcon.contains(e.target)) {
            closeMenu();
        }
    });
    
    // Cerrar menú con la tecla Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && menu.classList.contains('active')) {
            closeMenu();
        }
    });
    
    // Prevenir que el clic en el menú se propague al documento
    menu.addEventListener('click', (e) => {
        e.stopPropagation();
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







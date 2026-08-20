// Encapsulamos todo el código para evitar variables globales
(function() {
let menuIcon, menu, navbar;
let lastScrollY = window.scrollY;

function initMainInteractions() {
    // Swiper para testimonios (protegido si la librería aún no está cargada)
    let swiper = null;
    if (typeof Swiper === 'function') {
        swiper = new Swiper('.swiper', {
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
        if (swiperContainer) {
            swiperContainer.addEventListener('mouseenter', () => {
                swiper.autoplay.stop();
            });
            swiperContainer.addEventListener('mouseleave', () => {
                swiper.autoplay.start();
            });
        }
    } else {
        console.warn('Swiper no está disponible aún; se omite la animación de testimonios.');
    }

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

    // MENÚ HAMBURGUESA - FUNCIONALIDAD COMPLETA
    menuIcon = document.querySelector('.menu-icon');
    menu = document.querySelector('.menu');
    navbar = document.querySelector('.navbar');
    
    if (!menuIcon || !menu) {
        console.warn('Elementos del menú no encontrados');
        return;
    }
    
    // Toggle del menú hamburguesa (forzando estilos en móvil para evitar conflictos de CSS)
    menuIcon.addEventListener('click', function(e) {
        e.preventDefault();
        const isActive = menu.classList.toggle('active');
        menuIcon.classList.toggle('active');

        if (isActive) {
            menu.style.display = 'flex';
            menu.style.flexDirection = 'column';
        } else {
            menu.style.display = '';
            menu.style.flexDirection = '';
        }
        
        // Actualizar aria-expanded para accesibilidad
        menuIcon.setAttribute('aria-expanded', isActive ? 'true' : 'false');
    });
    
    // Cerrar menú al hacer clic en un enlace
    const menuLinks = document.querySelectorAll('.menu li a');
    menuLinks.forEach(link => {
        link.addEventListener('click', () => {
            menu.classList.remove('active');
            menuIcon.classList.remove('active');
            menuIcon.setAttribute('aria-expanded', 'false');
        });
    });
    
    // Cerrar menú al hacer clic fuera de él
    document.addEventListener('click', function(e) {
        if (menu.classList.contains('active') && 
            !menu.contains(e.target) && 
            !menuIcon.contains(e.target)) {
            menu.classList.remove('active');
            menuIcon.classList.remove('active');
            menuIcon.setAttribute('aria-expanded', 'false');
        }
    });
}

// Ejecutar inmediatamente si el DOM ya está listo, o esperar al evento si aún está cargando
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMainInteractions);
} else {
    initMainInteractions();
}

// Navbar auto-hide al hacer scroll
window.addEventListener('scroll', () => {
    if (!navbar || !menu) return;
    
    // No ocultar navbar si el menú está abierto
    if (menu.classList.contains('active')) {
        lastScrollY = window.scrollY;
        return;
    }
    
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







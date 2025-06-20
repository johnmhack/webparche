//codigo para los botones de la paginacion

document.addEventListener('DOMContentLoaded', () => {
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
});

//codigo para las preguntas frecuentes, para dale movimiento tanto a la flecha y las casillas

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

// CODIGO PARA EL BOTON DEL MENU DE HAMBURGUESA

document.addEventListener('DOMContentLoaded', () => {
    const menuIcon = document.querySelector('.menu-icon');
    const menu = document.querySelector('.menu');

    // Verifica si los elementos existen en el DOM
    if (!menuIcon || !menu) {
        console.error('Error: No se encuentran los elementos .menu-icon o .menu en el DOM.');
        return;
    }

    // Evento para alternar la visibilidad del menú
    menuIcon.addEventListener('click', () => {
        menu.classList.toggle('active'); // Activa/desactiva la clase 'active'
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







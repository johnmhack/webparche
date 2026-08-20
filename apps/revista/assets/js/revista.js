// Revista Parche - Efectos estilo GTA VI con GSAP

document.addEventListener('DOMContentLoaded', function() {
    // Registrar plugins de GSAP
    gsap.registerPlugin(ScrollTrigger);

    // ============================================
    // HERO SECTION - Animación de entrada
    // ============================================
    const heroTitle = document.querySelector('.hero-title');
    const heroSubtitle = document.querySelector('.hero-subtitle');
    const heroScroll = document.querySelector('.hero-scroll-indicator');

    if (heroTitle && heroSubtitle && heroScroll) {
        gsap.timeline()
            .to(heroTitle, {
                opacity: 1,
                y: 0,
                duration: 1.5,
                ease: "power3.out"
            })
            .to(heroSubtitle, {
                opacity: 1,
                y: 0,
                duration: 1,
                ease: "power2.out"
            }, "-=0.5")
            .to(heroScroll, {
                opacity: 1,
                duration: 1,
                ease: "power2.out"
            }, "-=0.5");
    }

    // ============================================
    // FEATURED ARTICLE - Parallax y efectos
    // ============================================
    const featuredImage = document.querySelector('.featured-image');
    const featuredOverlay = document.querySelector('.featured-overlay');
    const featuredContent = document.querySelector('.featured-content');

    if (featuredImage && featuredOverlay && featuredContent) {
        // Parallax en la imagen
        gsap.to(featuredImage, {
            scrollTrigger: {
                trigger: featuredImage,
                start: "top bottom",
                end: "bottom top",
                scrub: 1
            },
            scale: 1.3,
            ease: "none"
        });

        // Fade in del contenido
        gsap.from(featuredContent, {
            scrollTrigger: {
                trigger: featuredContent,
                start: "top 80%",
                toggleActions: "play none none reverse"
            },
            opacity: 0,
            x: -50,
            duration: 1,
            ease: "power3.out"
        });

        // Overlay que aparece al hacer scroll
        gsap.to(featuredOverlay, {
            scrollTrigger: {
                trigger: featuredImage,
                start: "top 60%",
                end: "bottom 40%",
                scrub: true
            },
            opacity: 1,
            ease: "none"
        });
    }

    // ============================================
    // ARTICLES SECTION - Scroll vertical con parallax
    // ============================================
    const articleItems = document.querySelectorAll('.article-item');

    articleItems.forEach((item, index) => {
        const image = item.querySelector('.article-image');
        const overlay = item.querySelector('.article-overlay');
        const content = item.querySelector('.article-content');

        // Parallax en cada imagen
        if (image) {
            gsap.to(image, {
                scrollTrigger: {
                    trigger: item,
                    start: "top bottom",
                    end: "bottom top",
                    scrub: 1
                },
                scale: 1.4,
                ease: "none"
            });
        }

        // Fade in del contenido desde diferentes direcciones
        if (content) {
            const direction = index % 2 === 0 ? 50 : -50;
            gsap.from(content, {
                scrollTrigger: {
                    trigger: item,
                    start: "top 75%",
                    toggleActions: "play none none reverse"
                },
                opacity: 0,
                x: direction,
                duration: 1.2,
                ease: "power3.out"
            });
        }

        // Overlay que aparece al hacer scroll
        if (overlay) {
            gsap.to(overlay, {
                scrollTrigger: {
                    trigger: item,
                    start: "top 60%",
                    end: "bottom 40%",
                    scrub: true
                },
                opacity: 1,
                ease: "none"
            });
        }

        // Efecto de pin en cada artículo (opcional, estilo GTA VI)
        ScrollTrigger.create({
            trigger: item,
            start: "top top",
            end: "bottom top",
            pin: false,
            anticipatePin: 1
        });
    });

    // ============================================
    // CHARACTER SECTION - Efectos estilo GTA VI
    // ============================================
    const characterImage = document.querySelector('.character-image');
    const characterOverlay = document.querySelector('.character-overlay');
    const characterContent = document.querySelector('.character-content');

    if (characterImage && characterOverlay && characterContent) {
        // Parallax intenso en la imagen del personaje
        gsap.to(characterImage, {
            scrollTrigger: {
                trigger: characterImage,
                start: "top bottom",
                end: "bottom top",
                scrub: 1
            },
            scale: 1.3,
            y: -100,
            ease: "none"
        });

        // Fade in del contenido del personaje
        gsap.from(characterContent, {
            scrollTrigger: {
                trigger: characterContent,
                start: "top 80%",
                toggleActions: "play none none reverse"
            },
            opacity: 0,
            x: 50,
            duration: 1.5,
            ease: "power3.out"
        });

        // Overlay que aparece progresivamente
        gsap.to(characterOverlay, {
            scrollTrigger: {
                trigger: characterImage,
                start: "top 50%",
                end: "bottom 50%",
                scrub: true
            },
            opacity: 1,
            ease: "none"
        });
    }

    // ============================================
    // EFECTOS ADICIONALES - Smooth scroll
    // ============================================
    // Smooth scroll para toda la página
    gsap.to("body", {
        scrollBehavior: "smooth",
        duration: 0
    });

    // Efecto de cursor personalizado (opcional)
    const cursor = document.createElement('div');
    cursor.className = 'custom-cursor';
    cursor.style.cssText = `
        position: fixed;
        width: 20px;
        height: 20px;
        border: 2px solid var(--revista-accent);
        border-radius: 50%;
        pointer-events: none;
        z-index: 10000;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    document.body.appendChild(cursor);

    document.addEventListener('mousemove', (e) => {
        gsap.to(cursor, {
            x: e.clientX - 10,
            y: e.clientY - 10,
            duration: 0.3,
            ease: "power2.out"
        });
        cursor.style.opacity = '1';
    });

    document.addEventListener('mouseleave', () => {
        cursor.style.opacity = '0';
    });

    console.log('✨ Revista Parche - Efectos GTA VI activados ✨');
});

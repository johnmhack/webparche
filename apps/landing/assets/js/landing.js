/* Efectos landing Parche v2 — contadores y aparición al scroll */
(function () {
  if (!document.body.classList.contains('landing-v2')) return;

  /* Contador de números (+5, +100, +50) */
  function animateCounter(el) {
    if (el.dataset.animated === 'true') return;
    el.dataset.animated = 'true';

    const target = parseInt(el.dataset.count || el.textContent.replace(/\D/g, ''), 10);
    if (!target) return;

    const duration = 1800;
    const start = performance.now();

    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = '+' + Math.round(target * eased);
      if (progress < 1) requestAnimationFrame(tick);
    }

    el.textContent = '+0';
    requestAnimationFrame(tick);
  }

  const counters = document.querySelectorAll('.guarantee .info h3');
  if (counters.length && 'IntersectionObserver' in window) {
    const counterObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            counterObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 }
    );
    counters.forEach((el) => counterObserver.observe(el));
  }

  /* Aparición suave al hacer scroll */
  const revealSelectors = [
    '.service-list li',
    '.guarantee .item',
    '.torker__content',
    '.testimonial__card',
    '.faq-item',
    '.download-band',
  ];

  const revealEls = document.querySelectorAll(revealSelectors.join(','));
  revealEls.forEach((el) => el.classList.add('reveal-on-scroll'));

  if (revealEls.length && 'IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    revealEls.forEach((el) => revealObserver.observe(el));
  }
})();

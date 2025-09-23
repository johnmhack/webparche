// JavaScript específico para la Revista

document.addEventListener('DOMContentLoaded', function() {
    console.log('Revista Parche cargada');

    // Funcionalidad específica de la revista
    // Ejemplo: cargar artículos dinámicamente, filtros, etc.

    // Función para cargar más artículos (placeholder)
    function loadMoreArticles() {
        // Implementación futura
        console.log('Cargando más artículos...');
    }

    // Event listeners para artículos
    const articleCards = document.querySelectorAll('.article-card');
    articleCards.forEach(card => {
        card.addEventListener('click', function() {
            // Implementar navegación a artículo completo
            console.log('Artículo clickeado:', this.querySelector('h3, h4').textContent);
        });
    });
});
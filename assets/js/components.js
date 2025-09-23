// Componentes JavaScript reutilizables globales
// Ejemplo: funciones para modales, validaciones, etc.

// Función para mostrar notificaciones
function showGlobalNotification(message, type = 'info') {
    // Implementación básica
    console.log(`${type}: ${message}`);
}

// Función para validar emails
function validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}
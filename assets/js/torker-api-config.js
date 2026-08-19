/**
 * URL base del API Torker.
 * Desarrollo: abre el dashboard en http://127.0.0.1:8000/pages/dashboard/
 */
(function () {
  const host = window.location.hostname;
  const port = window.location.port;

  if (window.location.protocol === 'file:') {
    window.TORKER_API_BASE = 'http://127.0.0.1:8000/api';
    console.warn(
      '[Torker] Abre con Django: http://127.0.0.1:8000/pages/dashboard/ (file:// no funciona)'
    );
    return;
  }

  if (host === 'localhost' || host === '127.0.0.1') {
    // Mismo origen si ya estás en runserver :8000
    window.TORKER_API_BASE =
      port === '8000' ? `${window.location.origin}/api` : `http://${host}:8000/api`;
    return;
  }

  window.TORKER_API_BASE = `${window.location.origin}/api`;
})();

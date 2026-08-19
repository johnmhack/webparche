/**
 * URL base del API Torker (sin Railway).
 * - Local / file: Django en 127.0.0.1:8000
 * - Producción: /api en el mismo dominio (proxy cuando despliegues el backend)
 */
(function () {
  const host = window.location.hostname;
  const isLocal =
    host === 'localhost' ||
    host === '127.0.0.1' ||
    window.location.protocol === 'file:';

  window.TORKER_API_BASE = isLocal
    ? 'http://127.0.0.1:8000/api'
    : `${window.location.origin}/api`;
})();

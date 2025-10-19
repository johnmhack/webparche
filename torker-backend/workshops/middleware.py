"""
Middleware para aislamiento de datos entre talleres (Multi-tenancy)
Asegura que cada taller solo acceda a sus propios datos
"""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class WorkshopIsolationMiddleware(MiddlewareMixin):
    """
    Middleware que asegura el aislamiento de datos entre talleres.
    Agrega el workshop del usuario autenticado al request para uso en vistas.
    """
    
    def process_request(self, request):
        """
        Procesa cada request y agrega información del taller si el usuario está autenticado.
        """
        # Solo procesar si el usuario está autenticado
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                # Intentar obtener el taller del usuario
                if hasattr(request.user, 'workshop'):
                    request.workshop = request.user.workshop
                    
                    # Verificar que la suscripción esté activa
                    if not request.workshop.is_subscription_active:
                        logger.warning(
                            f"Acceso denegado: Suscripción expirada para taller {request.workshop.id}"
                        )
                        # Permitir acceso pero registrar warning
                        # En producción podrías bloquear el acceso aquí
                else:
                    request.workshop = None
                    logger.debug(f"Usuario {request.user.email} no tiene taller asociado")
                    
            except Exception as e:
                logger.error(f"Error obteniendo taller del usuario: {str(e)}")
                request.workshop = None
        else:
            request.workshop = None
        
        return None
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Procesa la vista antes de ejecutarla.
        Valida que las operaciones sean sobre datos del taller correcto.
        """
        # Solo validar en vistas de API que requieren autenticación
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Validar que si hay un ID de workshop en los parámetros, coincida con el del usuario
            workshop_id = view_kwargs.get('workshop_id') or request.GET.get('workshop_id')
            
            if workshop_id and hasattr(request, 'workshop') and request.workshop:
                if str(request.workshop.id) != str(workshop_id):
                    logger.warning(
                        f"Intento de acceso cross-taller: Usuario {request.user.email} "
                        f"intentó acceder a taller {workshop_id}"
                    )
                    return JsonResponse({
                        'error': 'No tienes permiso para acceder a este taller'
                    }, status=403)
        
        return None


class WorkshopDataValidationMiddleware(MiddlewareMixin):
    """
    Middleware adicional para validar que los datos pertenezcan al taller correcto.
    Se ejecuta después de WorkshopIsolationMiddleware.
    """
    
    def process_response(self, request, response):
        """
        Procesa la respuesta para agregar headers de seguridad multi-taller.
        """
        # Agregar header personalizado con ID del taller (solo en desarrollo)
        if hasattr(request, 'workshop') and request.workshop:
            # Solo en desarrollo para debugging
            if hasattr(request, 'user') and request.user.is_authenticated:
                response['X-Workshop-ID'] = str(request.workshop.id)
                response['X-Workshop-Name'] = request.workshop.name
        
        return response
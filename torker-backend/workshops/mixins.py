"""
Mixins para ViewSets con aislamiento de datos multi-taller
"""
from rest_framework import status
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


class WorkshopFilterMixin:
    """
    Mixin que asegura que todos los queries filtren por el taller del usuario autenticado.
    Previene acceso cross-taller en operaciones CRUD.
    """
    
    def get_queryset(self):
        """
        Sobrescribe get_queryset para filtrar siempre por workshop del usuario.
        """
        queryset = super().get_queryset()
        
        # Verificar que el usuario tenga taller
        if not hasattr(self.request.user, 'workshop'):
            logger.warning(f"Usuario {self.request.user.email} sin taller intentó acceder a datos")
            return queryset.none()  # Retornar queryset vacío
        
        workshop = self.request.user.workshop
        
        # Filtrar por workshop si el modelo tiene ese campo
        if hasattr(queryset.model, 'workshop'):
            queryset = queryset.filter(workshop=workshop)
            logger.debug(f"Query filtrado por workshop: {workshop.id}")
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Sobrescribe perform_create para asignar automáticamente el workshop.
        """
        # Verificar que el usuario tenga taller
        if not hasattr(self.request.user, 'workshop'):
            raise ValueError("Usuario sin taller asociado")
        
        workshop = self.request.user.workshop
        
        # Verificar que la suscripción esté activa
        if not workshop.is_subscription_active:
            raise ValueError("Suscripción del taller expirada")
        
        # Guardar con workshop asignado
        serializer.save(workshop=workshop)
        logger.info(f"Objeto creado para workshop: {workshop.id}")
    
    def perform_update(self, serializer):
        """
        Sobrescribe perform_update para validar que el objeto pertenece al taller.
        """
        instance = self.get_object()
        
        # Validar que el objeto pertenece al taller del usuario
        if hasattr(instance, 'workshop'):
            if instance.workshop != self.request.user.workshop:
                logger.warning(
                    f"Intento de actualización cross-taller: "
                    f"Usuario {self.request.user.email} intentó modificar objeto de taller {instance.workshop.id}"
                )
                raise ValueError("No tienes permiso para modificar este objeto")
        
        serializer.save()
        logger.info(f"Objeto actualizado para workshop: {self.request.user.workshop.id}")
    
    def perform_destroy(self, instance):
        """
        Sobrescribe perform_destroy para validar que el objeto pertenece al taller.
        """
        # Validar que el objeto pertenece al taller del usuario
        if hasattr(instance, 'workshop'):
            if instance.workshop != self.request.user.workshop:
                logger.warning(
                    f"Intento de eliminación cross-taller: "
                    f"Usuario {self.request.user.email} intentó eliminar objeto de taller {instance.workshop.id}"
                )
                raise ValueError("No tienes permiso para eliminar este objeto")
        
        instance.delete()
        logger.info(f"Objeto eliminado para workshop: {self.request.user.workshop.id}")


class SubscriptionValidationMixin:
    """
    Mixin que valida que la suscripción del taller esté activa antes de operaciones críticas.
    """
    
    def check_subscription(self):
        """
        Verifica que la suscripción del taller esté activa.
        """
        if not hasattr(self.request.user, 'workshop'):
            return False, "Usuario sin taller asociado"
        
        workshop = self.request.user.workshop
        
        if not workshop.is_subscription_active:
            days_expired = (workshop.subscription_expires - timezone.now().date()).days
            return False, f"Suscripción expirada hace {abs(days_expired)} días"
        
        return True, "Suscripción activa"
    
    def create(self, request, *args, **kwargs):
        """
        Sobrescribe create para validar suscripción antes de crear.
        """
        is_valid, message = self.check_subscription()
        if not is_valid:
            return Response({
                'error': message,
                'subscription_expired': True
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        return super().create(request, *args, **kwargs)


class AuditLogMixin:
    """
    Mixin que registra auditoría de operaciones críticas.
    """
    
    def log_action(self, action, instance, extra_data=None):
        """
        Registra una acción en el log de auditoría.
        
        Args:
            action: Tipo de acción ('create', 'update', 'delete', 'view')
            instance: Instancia del modelo afectado
            extra_data: Datos adicionales para el log
        """
        log_data = {
            'user': self.request.user.email,
            'workshop': self.request.user.workshop.id if hasattr(self.request.user, 'workshop') else None,
            'action': action,
            'model': instance.__class__.__name__,
            'instance_id': str(instance.id) if hasattr(instance, 'id') else None,
            'ip_address': self.get_client_ip(),
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        logger.info(f"AUDIT: {log_data}")
    
    def get_client_ip(self):
        """Obtiene la IP del cliente desde el request."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def perform_create(self, serializer):
        """Registra auditoría al crear."""
        instance = serializer.save()
        self.log_action('create', instance)
        return instance
    
    def perform_update(self, serializer):
        """Registra auditoría al actualizar."""
        instance = serializer.save()
        self.log_action('update', instance)
        return instance
    
    def perform_destroy(self, instance):
        """Registra auditoría al eliminar."""
        self.log_action('delete', instance)
        instance.delete()
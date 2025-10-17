from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
import uuid
import hashlib
from decimal import Decimal


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo User"""

    def create_user(self, email, password=None, **extra_fields):
        """Crear usuario regular"""
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)  # Username = email
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crear superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Usuario personalizado para dueños de talleres"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    # Resolver conflictos con el modelo User por defecto de Django
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='workshop_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='workshop_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"


class Workshop(models.Model):
    """Información del taller"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='workshop')
    name = models.CharField(max_length=255)
    # Información fiscal del taller (para facturación)
    nit = models.CharField(max_length=20, unique=True, blank=True, null=True)
    legal_name = models.CharField(max_length=255, blank=True)  # Razón social
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)

    # Información tributaria
    TAX_REGIME_CHOICES = [
        ('comun', 'Régimen Común'),
        ('simplificado', 'Régimen Simplificado'),
        ('especial', 'Régimen Especial'),
    ]
    tax_regime = models.CharField(max_length=20, choices=TAX_REGIME_CHOICES, default='comun')

    # Resolución DIAN
    dian_resolution_number = models.CharField(max_length=50, blank=True)
    dian_resolution_date = models.DateField(null=True, blank=True)
    dian_resolution_expires = models.DateField(null=True, blank=True)
    invoice_prefix = models.CharField(max_length=10, default='F')  # Prefijo para facturas

    # Configuración de facturación
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=19.00)  # IVA por defecto
    invoice_footer = models.TextField(blank=True)  # Texto pie de página facturas
    payment_terms = models.TextField(blank=True)  # Términos de pago

    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)

    # Sistema de suscripciones
    SUBSCRIPTION_PLANS = [
        ('trial', 'Prueba Gratuita'),
        ('basic', 'Básico'),
        ('premium', 'Premium'),
    ]
    subscription_plan = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_PLANS,
        default='trial'
    )
    subscription_expires = models.DateField(
        default=timezone.now() + timezone.timedelta(days=30)
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workshops'

    def __str__(self):
        return self.name

    @property
    def is_subscription_active(self):
        return self.subscription_expires >= timezone.now() and self.is_active


class Mechanic(models.Model):
    """Mecánicos especializados del taller"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='mechanics')

    # Información personal
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # Identificación
    DOCUMENT_TYPE_CHOICES = [
        ('cc', 'Cédula de Ciudadanía'),
        ('ce', 'Cédula de Extranjería'),
        ('nit', 'NIT'),
        ('ti', 'Tarjeta de Identidad'),
        ('pasaporte', 'Pasaporte'),
        ('other', 'Otro'),
    ]
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='cc')
    document_number = models.CharField(max_length=20, blank=True)

    # Especialización y experiencia
    SPECIALIZATION_CHOICES = [
        ('general', 'Mecánico General'),
        ('motorcycle', 'Especialista en Motocicletas'),
        ('engine', 'Motor y Transmisión'),
        ('electrical', 'Sistema Eléctrico'),
        ('brakes', 'Frenos y Suspensión'),
        ('bodywork', 'Carrocería y Pintura'),
        ('diagnostic', 'Diagnóstico Electrónico'),
        ('maintenance', 'Mantenimiento Preventivo'),
    ]
    specialization = models.CharField(max_length=20, choices=SPECIALIZATION_CHOICES, default='general')

    # Nivel de experiencia
    EXPERIENCE_LEVEL_CHOICES = [
        ('junior', 'Principiante (0-2 años)'),
        ('intermediate', 'Intermedio (2-5 años)'),
        ('senior', 'Senior (5-10 años)'),
        ('expert', 'Experto (10+ años)'),
    ]
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default='junior')

    # Información laboral
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Disponibilidad y carga de trabajo
    is_available = models.BooleanField(default=True)
    max_daily_hours = models.IntegerField(default=8)
    current_workload = models.IntegerField(default=0)  # Horas asignadas actualmente

    # Certificaciones y capacitación
    certifications = models.TextField(blank=True, help_text="Certificaciones obtenidas")
    training_completed = models.TextField(blank=True, help_text="Capacitaciones realizadas")

    # Estadísticas de rendimiento
    total_work_orders = models.IntegerField(default=0)
    completed_work_orders = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    # Estado
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mechanics'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_specialization_display()}"

    @property
    def full_name(self):
        """Nombre completo del mecánico"""
        return f"{self.first_name} {self.last_name}"

    @property
    def completion_rate(self):
        """Tasa de completación de órdenes de trabajo"""
        if self.total_work_orders > 0:
            return (self.completed_work_orders / self.total_work_orders) * 100
        return 0

    @property
    def available_hours_today(self):
        """Horas disponibles para trabajar hoy"""
        return max(0, self.max_daily_hours - self.current_workload)

    @property
    def is_overloaded(self):
        """Verificar si el mecánico está sobrecargado"""
        return self.current_workload > self.max_daily_hours

    @property
    def performance_score(self):
        """Puntuación de rendimiento basada en múltiples factores"""
        score = 0

        # Completación de trabajos (40%)
        score += (self.completion_rate / 100) * 40

        # Calificación promedio (30%)
        score += (self.average_rating / 5) * 30

        # Experiencia (20%)
        experience_weights = {
            'junior': 20,
            'intermediate': 40,
            'senior': 70,
            'expert': 100
        }
        score += experience_weights.get(self.experience_level, 0) * 0.2

        # Disponibilidad (10%)
        availability_bonus = 10 if self.is_available and not self.is_overloaded else 0
        score += availability_bonus

        return min(100, score)  # Máximo 100 puntos


# Mantener compatibilidad - Employee ahora hereda de Mechanic para mecánicos
class Employee(models.Model):
    """Empleados del taller (mecánicos, administradores, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='employees')

    # Información básica
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)  # Opcional
    phone = models.CharField(max_length=20, blank=True)

    # Rol y especialización
    ROLE_CHOICES = [
        ('mechanic', 'Mecánico'),
        ('admin', 'Administrador'),
        ('receptionist', 'Recepcionista'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='mechanic')
    specialization = models.CharField(max_length=100, blank=True)  # Solo para mecánicos
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'employees'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_role_display()}"


class Customer(models.Model):
    """Clientes del taller"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='customers')

    # Información personal
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # Documento de identidad (para facturación)
    DOCUMENT_TYPE_CHOICES = [
        ('cc', 'Cédula de Ciudadanía'),
        ('ce', 'Cédula de Extranjería'),
        ('nit', 'NIT'),
        ('ti', 'Tarjeta de Identidad'),
        ('pasaporte', 'Pasaporte'),
        ('other', 'Otro'),
    ]
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='cc')
    document_number = models.CharField(max_length=20, blank=True)

    # Dirección completa (para facturación)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)

    # Información adicional
    total_visits = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_visit = models.DateTimeField(null=True, blank=True)

    # Estado
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'
        unique_together = ['workshop', 'document_type', 'document_number']  # Un cliente único por taller

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_document_type_display()} {self.document_number}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self):
        """Dirección completa formateada"""
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.department:
            parts.append(self.department)
        return ", ".join(parts)


class Vehicle(models.Model):
    """Vehículos de los clientes (genérico para cualquier tipo de vehículo)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='vehicles')
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='vehicles')

    # Información básica del vehículo
    VEHICLE_TYPE_CHOICES = [
        ('motorcycle', 'Motocicleta'),
        ('car', 'Automóvil'),
        ('truck', 'Camión'),
        ('bicycle', 'Bicicleta'),
        ('other', 'Otro'),
    ]
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default='motorcycle')

    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    color = models.CharField(max_length=50, blank=True)

    # Identificación del vehículo
    license_plate = models.CharField(max_length=15, blank=True, help_text="Placa o matrícula")
    vin = models.CharField(max_length=17, blank=True, help_text="Número de chasis/VIN")
    engine_number = models.CharField(max_length=50, blank=True)

    # Especificaciones técnicas
    mileage = models.IntegerField(default=0, help_text="Kilometraje actual")

    FUEL_CHOICES = [
        ('gasolina', 'Gasolina'),
        ('diesel', 'Diésel'),
        ('electrico', 'Eléctrico'),
        ('hibrido', 'Híbrido'),
        ('gas', 'Gas Natural'),
        ('other', 'Otro'),
    ]
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='gasolina')

    TRANSMISSION_CHOICES = [
        ('manual', 'Manual'),
        ('automatico', 'Automático'),
        ('cvt', 'CVT'),
        ('semi-automatico', 'Semi-automático'),
    ]
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, default='manual')

    # Información adicional
    cylinder_capacity = models.IntegerField(null=True, blank=True, help_text="Cilindraje en CC")
    doors = models.IntegerField(null=True, blank=True, help_text="Número de puertas")
    passengers = models.IntegerField(null=True, blank=True, help_text="Número de pasajeros")

    # Historial y mantenimiento
    last_service_date = models.DateField(null=True, blank=True)
    next_service_mileage = models.IntegerField(null=True, blank=True)
    next_service_date = models.DateField(null=True, blank=True)

    # Estado del vehículo
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, help_text="Observaciones sobre el vehículo")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vehicles'
        unique_together = ['workshop', 'vin']  # VIN único por taller (si existe)
        ordering = ['-updated_at']

    def __str__(self):
        plate_info = f" - {self.license_plate}" if self.license_plate else ""
        return f"{self.get_vehicle_type_display()}: {self.brand} {self.model} {self.year}{plate_info}"

    @property
    def full_name(self):
        """Nombre completo del vehículo"""
        return f"{self.brand} {self.model} {self.year}"

    @property
    def needs_service(self):
        """Verificar si el vehículo necesita mantenimiento"""
        today = timezone.now().date()
        if self.next_service_date and today >= self.next_service_date:
            return True
        if self.next_service_mileage and self.mileage >= self.next_service_mileage:
            return True
        return False

    @property
    def service_status(self):
        """Estado del servicio del vehículo"""
        if not self.needs_service:
            return "ok"
        elif self.next_service_date and timezone.now().date() > self.next_service_date:
            return "overdue"
        else:
            return "due_soon"


# Mantener compatibilidad hacia atrás - Motorcycle ahora hereda de Vehicle
class Motorcycle(Vehicle):
    """Motos de los clientes (hereda de Vehicle para compatibilidad)"""
    class Meta:
        proxy = True  # No crea tabla nueva, usa la de Vehicle

    def save(self, *args, **kwargs):
        self.vehicle_type = 'motorcycle'
        super().save(*args, **kwargs)


class Service(models.Model):
    """Catálogo de servicios ofrecidos por el taller"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='services')

    # Información básica del servicio
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    service_code = models.CharField(max_length=50, blank=True)  # Código interno del servicio

    # Categorización
    CATEGORY_CHOICES = [
        ('maintenance', 'Mantenimiento'),
        ('repair', 'Reparación'),
        ('diagnostic', 'Diagnóstico'),
        ('emergency', 'Emergencia'),
        ('modification', 'Modificación'),
        ('inspection', 'Inspección'),
        ('cleaning', 'Limpieza'),
        ('other', 'Otro'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='repair')

    # Tipo de vehículo aplicable
    VEHICLE_TYPE_CHOICES = [
        ('motorcycle', 'Motocicleta'),
        ('car', 'Automóvil'),
        ('truck', 'Camión'),
        ('all', 'Todos los tipos'),
    ]
    applicable_vehicle_types = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default='motorcycle')

    # Estimaciones de tiempo y costo
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=2, default=1)  # Horas estimadas
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Precio base
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # Tarifa por hora adicional

    # Requisitos y compatibilidad
    required_skills = models.CharField(max_length=100, blank=True)  # Habilidades requeridas
    compatible_brands = models.TextField(blank=True)  # JSON con marcas compatibles
    required_tools = models.TextField(blank=True)  # Herramientas necesarias

    # Información adicional
    warranty_months = models.IntegerField(default=0)  # Garantía en meses
    priority_level = models.IntegerField(default=3, choices=[(1, 'Baja'), (2, 'Media'), (3, 'Alta'), (4, 'Urgente')])

    # Estado y configuración
    is_active = models.BooleanField(default=True)
    is_taxable = models.BooleanField(default=True)  # Si aplica IVA
    requires_approval = models.BooleanField(default=False)  # Requiere aprobación especial

    # Estadísticas de uso
    times_used = models.IntegerField(default=0)  # Veces utilizado
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)  # Calificación promedio
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Ingresos totales generados

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'services'
        unique_together = ['workshop', 'service_code']  # Código único por taller
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} - {self.get_category_display()}"

    @property
    def estimated_cost(self):
        """Costo estimado total del servicio"""
        return self.base_price + (self.estimated_hours * self.hourly_rate)

    @property
    def is_popular(self):
        """Verificar si el servicio es popular"""
        return self.times_used >= 10

    @property
    def profit_margin(self):
        """Margen de ganancia promedio (si hay datos suficientes)"""
        if self.times_used > 0 and self.total_revenue > 0:
            avg_cost = self.estimated_cost
            if avg_cost > 0:
                return ((self.total_revenue - (avg_cost * self.times_used)) / (avg_cost * self.times_used)) * 100
        return 0

    def update_statistics(self, rating=None, revenue=None):
        """Actualizar estadísticas del servicio"""
        if rating is not None:
            # Calcular nueva calificación promedio
            total_ratings = self.times_used
            current_total = self.average_rating * total_ratings
            new_total = current_total + rating
            self.average_rating = new_total / (total_ratings + 1)

        if revenue is not None:
            self.total_revenue += revenue

        self.times_used += 1
        self.save()


class SparePart(models.Model):
    """Inventario de repuestos del taller"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='spare_parts')

    # Información básica
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    part_number = models.CharField(max_length=100, blank=True)
    internal_code = models.CharField(max_length=50, blank=True)  # Código interno único

    # Categorización
    CATEGORY_CHOICES = [
        ('motor', 'Motor'),
        ('transmision', 'Transmisión'),
        ('frenos', 'Frenos'),
        ('suspension', 'Suspensión'),
        ('electrico', 'Sistema Eléctrico'),
        ('carroceria', 'Carrocería'),
        ('accesorios', 'Accesorios'),
        ('lubricantes', 'Lubricantes'),
        ('filtros', 'Filtros'),
        ('neumaticos', 'Neumáticos'),
        ('other', 'Otro'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')

    # Marca y compatibilidad
    brand = models.CharField(max_length=100, blank=True)
    compatible_models = models.TextField(blank=True)  # JSON con modelos compatibles
    applicable_vehicle_types = models.CharField(max_length=20, choices=Service.VEHICLE_TYPE_CHOICES, default='motorcycle')

    # Inventario y precios
    stock_quantity = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=5)  # Nivel mínimo de stock
    max_stock_level = models.IntegerField(default=50)  # Nivel máximo recomendado
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Información adicional
    location = models.CharField(max_length=100, blank=True)  # Ubicación en el taller
    supplier = models.CharField(max_length=100, blank=True)
    supplier_code = models.CharField(max_length=50, blank=True)  # Código del proveedor
    warranty_months = models.IntegerField(default=0)

    # Dimensiones y peso (para logística)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    dimensions = models.CharField(max_length=50, blank=True)  # Ej: "30x20x10 cm"

    # Estado y configuración
    is_active = models.BooleanField(default=True)
    is_taxable = models.BooleanField(default=True)  # Si aplica IVA
    requires_special_storage = models.BooleanField(default=False)  # Almacenamiento especial

    # Estadísticas
    times_used = models.IntegerField(default=0)  # Veces utilizado en OT
    total_sold = models.IntegerField(default=0)  # Unidades vendidas
    last_sale_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'spare_parts'
        unique_together = ['workshop', 'internal_code']  # Código interno único por taller
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} - {self.internal_code or self.part_number} - Stock: {self.stock_quantity}"

    @property
    def profit_margin(self):
        """Margen de ganancia"""
        if self.unit_cost > 0:
            return ((self.sale_price - self.unit_cost) / self.unit_cost) * 100
        return 0

    @property
    def is_low_stock(self):
        """Verificar si el stock está bajo"""
        return self.stock_quantity <= self.min_stock_level

    @property
    def is_overstock(self):
        """Verificar si hay sobrestock"""
        return self.stock_quantity > self.max_stock_level

    @property
    def stock_value(self):
        """Valor total del stock"""
        return self.stock_quantity * self.unit_cost

    @property
    def turnover_rate(self):
        """Tasa de rotación (veces vendido por período)"""
        # Simplificado - en producción calcular por meses
        return self.total_sold / max(1, self.stock_quantity + self.total_sold)

    def update_stock(self, quantity_change, is_sale=False):
        """Actualizar stock y estadísticas"""
        self.stock_quantity += quantity_change

        if is_sale and quantity_change < 0:  # Venta (cantidad negativa)
            self.total_sold += abs(quantity_change)
            self.last_sale_date = timezone.now().date()

        self.save()


# Mantener compatibilidad - crear modelo Part que herede de SparePart
class Part(SparePart):
    """Modelo Part para compatibilidad hacia atrás con facturación DIAN"""
    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        # Asegurar que se guarde como SparePart
        super().save(*args, **kwargs)


class WorkOrder(models.Model):
    """Órdenes de trabajo principales"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='work_orders')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='work_orders')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='work_orders', null=True, blank=True)
    assigned_mechanic = models.ForeignKey(Mechanic, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_orders')

    # Numeración automática
    order_number = models.CharField(max_length=20, unique=True, editable=False)

    # Estados del flujo de trabajo
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('approved', 'Aprobada'),
        ('in_progress', 'En Progreso'),
        ('quality_check', 'Control de Calidad'),
        ('completed', 'Completada'),
        ('invoiced', 'Facturada'),
        ('cancelled', 'Cancelada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Información del trabajo
    title = models.CharField(max_length=200, help_text="Título breve del trabajo", default="Orden de Trabajo")
    description = models.TextField(blank=True, help_text="Descripción detallada del problema")
    symptoms = models.TextField(blank=True, help_text="Síntomas reportados por el cliente")
    diagnosis = models.TextField(blank=True, help_text="Diagnóstico realizado")

    # Prioridades y urgencia
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')

    # Estimaciones y costos
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    final_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Fechas importantes
    created_date = models.DateTimeField(default=timezone.now)
    approved_date = models.DateTimeField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    estimated_completion_date = models.DateTimeField(null=True, blank=True)
    actual_completion_date = models.DateTimeField(null=True, blank=True)

    # Información adicional
    mileage_at_entry = models.IntegerField(null=True, blank=True, help_text="Kilometraje al ingreso")
    mileage_at_exit = models.IntegerField(null=True, blank=True, help_text="Kilometraje al egreso")

    # Control de calidad
    quality_check_passed = models.BooleanField(default=False)
    quality_notes = models.TextField(blank=True)

    # Garantía
    warranty_period_months = models.IntegerField(default=0)
    warranty_start_date = models.DateField(null=True, blank=True)

    # Archivos y documentación
    photos_before = models.JSONField(blank=True, default=dict, help_text="URLs de fotos antes del trabajo")
    photos_after = models.JSONField(blank=True, default=dict, help_text="URLs de fotos después del trabajo")
    documents = models.JSONField(blank=True, default=dict, help_text="URLs de documentos adjuntos")
    description = models.TextField(blank=True, help_text="Descripción detallada del problema")

    # Notas y observaciones
    internal_notes = models.TextField(blank=True, help_text="Notas internas del taller")
    customer_notes = models.TextField(blank=True, help_text="Notas para el cliente")

    # Estadísticas y seguimiento
    total_services = models.IntegerField(default=0)
    total_parts = models.IntegerField(default=0)
    labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    parts_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'work_orders'
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['workshop', 'status']),
            models.Index(fields=['customer', 'created_date']),
            models.Index(fields=['assigned_mechanic', 'status']),
        ]

    def __str__(self):
        return f"OT-{self.order_number} - {self.customer.first_name} {self.customer.last_name} - {self.vehicle}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generar número de orden automático
            today = timezone.now().date()
            workshop_prefix = str(self.workshop.id)[:4].upper()
            # Contar órdenes del día para este taller
            daily_count = WorkOrder.objects.filter(
                workshop=self.workshop,
                created_at__date=today
            ).count() + 1
            self.order_number = f"OT{workshop_prefix}-{today.strftime('%Y%m%d')}-{daily_count:03d}"
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Verificar si la OT está atrasada"""
        if self.estimated_completion_date and self.status not in ['completed', 'cancelled', 'invoiced']:
            return timezone.now() > self.estimated_completion_date
        return False

    @property
    def days_overdue(self):
        """Días de atraso"""
        if self.is_overdue:
            return (timezone.now() - self.estimated_completion_date).days
        return 0

    @property
    def can_be_invoiced(self):
        """Verificar si la OT puede ser facturada"""
        return self.status == 'completed' and not hasattr(self, 'electronic_invoice')

    @property
    def status_color(self):
        """Color CSS según estado"""
        colors = {
            'draft': '#6b7280',      # gray
            'pending': '#f59e0b',    # amber
            'approved': '#3b82f6',   # blue
            'in_progress': '#f97316', # orange
            'quality_check': '#8b5cf6', # violet
            'completed': '#22c55e',  # green
            'invoiced': '#16a34a',   # dark green
            'cancelled': '#ef4444',  # red
        }
        return colors.get(self.status, '#6b7280')

    @property
    def progress_percentage(self):
        """Calcular porcentaje de progreso basado en estado e ítems completados"""
        # Progreso base por estado
        status_progress = {
            'draft': 0,
            'pending': 10,
            'approved': 20,
            'in_progress': 40,
            'quality_check': 80,
            'completed': 100,
            'invoiced': 100,
            'cancelled': 0,
        }

        base_progress = status_progress.get(self.status, 0)

        # Si está en progreso o control de calidad, calcular basado en ítems completados
        if self.status in ['in_progress', 'quality_check']:
            total_items = self.details.count()
            if total_items > 0:
                completed_items = self.details.filter(status='completed').count()
                items_progress = (completed_items / total_items) * 40  # 40% del progreso total
                base_progress = 40 + items_progress  # Estado base + progreso de ítems

        return min(100, base_progress)

    @property
    def total_cost(self):
        """Costo total actual (estimado o final)"""
        return self.final_cost if self.final_cost > 0 else self.estimated_cost

    @property
    def duration_days(self):
        """Duración total en días"""
        if self.actual_completion_date and self.start_date:
            return (self.actual_completion_date - self.start_date).days
        elif self.estimated_completion_date and self.start_date:
            return (self.estimated_completion_date - self.start_date).days
        return 0

    def update_costs(self):
        """Actualizar costos totales desde los items"""
        from django.db.models import Sum

        # Calcular costos desde WorkOrderItem
        totals = self.details.aggregate(
            total_labor=Sum('labor_cost', default=0),
            total_parts=Sum('parts_cost', default=0),
            total_services=Sum('service_quantity', default=0),
            total_parts_qty=Sum('part_quantity', default=0)
        )

        self.labor_cost = totals['total_labor'] or 0
        self.parts_cost = totals['total_parts'] or 0
        self.total_services = totals['total_services'] or 0
        self.total_parts = totals['total_parts_qty'] or 0
        self.final_cost = self.labor_cost + self.parts_cost
        self.save()

    def change_status(self, new_status, user=None, notes=None):
        """Cambiar estado con validaciones y logging"""
        from workshops.models import WorkOrderStatusLog

        # Validaciones de transición de estado
        valid_transitions = {
            'draft': ['pending', 'cancelled'],
            'pending': ['approved', 'in_progress', 'cancelled'],
            'approved': ['in_progress', 'cancelled'],
            'in_progress': ['quality_check', 'completed', 'cancelled'],
            'quality_check': ['completed', 'in_progress', 'cancelled'],
            'completed': ['invoiced'],
            'invoiced': [],  # Estado final
            'cancelled': [],  # Estado final
        }

        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(f"No se puede cambiar de {self.status} a {new_status}")

        old_status = self.status
        self.status = new_status

        # Actualizar fechas según el nuevo estado
        if new_status == 'approved' and not self.approved_date:
            self.approved_date = timezone.now()
        elif new_status == 'in_progress' and not self.start_date:
            self.start_date = timezone.now()
        elif new_status == 'completed' and not self.actual_completion_date:
            self.actual_completion_date = timezone.now()

        # Si se completa la OT, marcar todos los ítems como completados
        if new_status == 'completed':
            for item in self.details.all():
                if item.status != 'completed':
                    item.complete_item()

        # Actualizar horas reales si se completa
        if new_status == 'completed' and self.start_date and self.actual_completion_date:
            self.actual_hours = (self.actual_completion_date - self.start_date).total_seconds() / 3600

        self.save()

        # Crear log de cambio de estado
        WorkOrderStatusLog.objects.create(
            work_order=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=user,
            notes=notes
        )

        return True


class WorkOrderStatusLog(models.Model):
    """Log de cambios de estado de órdenes de trabajo"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(max_length=20, choices=WorkOrder.STATUS_CHOICES)
    new_status = models.CharField(max_length=20, choices=WorkOrder.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'work_order_status_logs'
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.work_order.order_number}: {self.old_status} → {self.new_status}"


# ===== MODELOS PARA FACTURACIÓN ELECTRÓNICA DIAN =====

class DianResolution(models.Model):
    """Control local de resoluciones de facturación DIAN"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='dian_resolutions')

    # Información de la resolución
    resolution_number = models.CharField(max_length=50, unique=True)  # Número de resolución
    resolution_date = models.DateField()  # Fecha de expedición
    expires_date = models.DateField()  # Fecha de vencimiento

    # Rango de numeración
    prefix = models.CharField(max_length=10, default='F')  # Prefijo (F, NC, ND, etc.)
    from_number = models.IntegerField()  # Número inicial
    to_number = models.IntegerField()  # Número final
    current_number = models.IntegerField(default=0)  # Número actual utilizado

    # Tipo de documento
    DOCUMENT_TYPE_CHOICES = [
        ('invoice', 'Factura Electrónica'),
        ('credit_note', 'Nota Crédito'),
        ('debit_note', 'Nota Débito'),
        ('equivalent', 'Documento Equivalente'),
    ]
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='invoice')

    # Estado
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dian_resolutions'
        unique_together = ['workshop', 'resolution_number']

    def __str__(self):
        return f"Resolución {self.resolution_number} - {self.workshop.name}"

    @property
    def is_valid(self):
        """Verificar si la resolución está vigente"""
        today = timezone.now().date()
        return self.is_active and self.expires_date >= today

    @property
    def available_numbers(self):
        """Números disponibles en la resolución"""
        return self.to_number - self.current_number

    @property
    def usage_percentage(self):
        """Porcentaje de uso de la resolución"""
        total_range = self.to_number - self.from_number + 1
        if total_range <= 0:
            return 0
        return (self.current_number / total_range) * 100

    @property
    def status(self):
        """Estado de la resolución basado en uso"""
        if not self.is_valid:
            return 'expired'
        if self.usage_percentage >= 90:
            return 'critical'
        elif self.usage_percentage >= 75:
            return 'warning'
        else:
            return 'ok'

    def get_next_number(self):
        """Obtener siguiente número disponible"""
        if not self.is_valid:
            raise ValueError("La resolución no está vigente")
        if self.current_number >= self.to_number:
            raise ValueError("No hay números disponibles en esta resolución")

        self.current_number += 1
        self.save()
        return f"{self.prefix}{self.current_number:04d}"

    def validate_invoice_number(self, invoice_number: str) -> bool:
        """Validar que un número de factura pertenece a esta resolución"""
        if not invoice_number.startswith(self.prefix):
            return False

        try:
            number_part = invoice_number[len(self.prefix):]
            number = int(number_part)
            return self.from_number <= number <= self.to_number
        except ValueError:
            return False

    def get_resolution_status(self):
        """Obtener estado completo de la resolución"""
        return {
            'resolution_number': self.resolution_number,
            'prefix': self.prefix,
            'range': f"{self.from_number}-{self.to_number}",
            'current': self.current_number,
            'available': self.available_numbers,
            'usage_percentage': round(self.usage_percentage, 2),
            'status': self.status,
            'is_valid': self.is_valid,
            'expires_date': self.expires_date,
            'days_until_expiry': (self.expires_date - timezone.now().date()).days if self.is_valid else 0
        }


class DianConfiguration(models.Model):
    """Configuración DIAN por taller"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.OneToOneField(Workshop, on_delete=models.CASCADE, related_name='dian_config')

    # Ambiente DIAN
    ENVIRONMENT_CHOICES = [
        ('test', 'Ambiente de Pruebas'),
        ('production', 'Ambiente de Producción'),
    ]
    environment = models.CharField(max_length=20, choices=ENVIRONMENT_CHOICES, default='test')

    # URLs de APIs DIAN
    test_webservice_url = models.URLField(default='https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc')
    production_webservice_url = models.URLField(default='https://vpfe.dian.gov.co/WcfDianCustomerServices.svc')

    # Credenciales de acceso
    test_username = models.CharField(max_length=100, blank=True)
    test_password = models.CharField(max_length=100, blank=True)
    production_username = models.CharField(max_length=100, blank=True)
    production_password = models.CharField(max_length=100, blank=True)

    # Configuración técnica
    software_id = models.CharField(max_length=100, default='710d99d0-6d49-4e18-bb70-196d1b17785f')  # ID del software
    software_pin = models.CharField(max_length=100, default='12345')  # PIN del software
    software_security_code = models.TextField(default='cfb3e564f5660585cd0ba4f23090242a73d3f4f298110d2eaa3976ce03cba4c6f980f6fa9a41b68a072d8e7decbd53a8')  # Código de seguridad

    # Configuración de firma digital
    signature_provider = models.CharField(max_length=50, default='camerfirma')  # camerfirma, etc.
    signature_username = models.CharField(max_length=100, blank=True)
    signature_password = models.CharField(max_length=100, blank=True)
    signature_certificate_id = models.CharField(max_length=100, blank=True)

    # Configuración adicional
    default_currency = models.CharField(max_length=3, default='COP')
    default_country = models.CharField(max_length=2, default='CO')
    default_language = models.CharField(max_length=2, default='es')

    # Configuración de validaciones
    enable_schematron_validation = models.BooleanField(default=True)
    enable_xml_validation = models.BooleanField(default=True)
    enable_dian_validation = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dian_configurations'

    def __str__(self):
        return f"Configuración DIAN - {self.workshop.name} ({self.environment})"

    @property
    def webservice_url(self):
        """URL del webservice según ambiente"""
        return self.test_webservice_url if self.environment == 'test' else self.production_webservice_url

    @property
    def username(self):
        """Username según ambiente"""
        return self.test_username if self.environment == 'test' else self.production_username

    @property
    def password(self):
        """Password según ambiente"""
        return self.test_password if self.environment == 'test' else self.production_password


class ElectronicInvoice(models.Model):
    """Factura electrónica DIAN"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='electronic_invoices')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='electronic_invoices')
    work_order = models.OneToOneField(WorkOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='electronic_invoice')

    # Numeración DIAN
    dian_resolution = models.ForeignKey(DianResolution, on_delete=models.PROTECT, related_name='invoices')
    invoice_number = models.CharField(max_length=20, unique=True)  # Número completo con prefijo
    consecutive_number = models.IntegerField()  # Número correlativo

    # CUDE (Código Único de Documento Electrónico)
    cude = models.CharField(max_length=96, unique=True, blank=True)  # SHA384

    # Fechas
    issue_date = models.DateTimeField(default=timezone.now)
    issue_time = models.TimeField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)

    # Información fiscal del taller
    workshop_nit = models.CharField(max_length=20)
    workshop_name = models.CharField(max_length=255)
    workshop_address = models.TextField()
    workshop_city = models.CharField(max_length=100)
    workshop_department = models.CharField(max_length=100)
    workshop_phone = models.CharField(max_length=20, blank=True)
    workshop_email = models.EmailField(blank=True)

    # Información del cliente
    customer_name = models.CharField(max_length=255)
    customer_document_type = models.CharField(max_length=20, choices=Customer.DOCUMENT_TYPE_CHOICES)
    customer_document = models.CharField(max_length=20)
    customer_address = models.TextField(blank=True)
    customer_city = models.CharField(max_length=100, blank=True)
    customer_department = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)

    # Totales
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=19.00)  # IVA Colombia
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Estado DIAN
    DIAN_STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('generated', 'XML Generado'),
        ('signed', 'Firmado'),
        ('sent', 'Enviado a DIAN'),
        ('accepted', 'Aceptado por DIAN'),
        ('rejected', 'Rechazado por DIAN'),
        ('cancelled', 'Cancelado'),
    ]
    dian_status = models.CharField(max_length=20, choices=DIAN_STATUS_CHOICES, default='draft')

    # Archivos XML
    xml_content = models.TextField(blank=True)  # XML sin firma
    signed_xml_content = models.TextField(blank=True)  # XML firmado
    qr_code_url = models.URLField(blank=True)  # URL completa del QR según DIAN
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)  # Imagen del QR generado

    # Respuestas DIAN
    dian_response_code = models.CharField(max_length=10, blank=True)
    dian_response_message = models.TextField(blank=True)
    dian_response_date = models.DateTimeField(null=True, blank=True)

    # Estado y pagos
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Pagada'),
        ('overdue', 'Vencida'),
        ('cancelled', 'Cancelada'),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Efectivo'),
        ('card', 'Tarjeta'),
        ('transfer', 'Transferencia'),
        ('check', 'Cheque'),
        ('other', 'Otro'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)

    # Notas y observaciones
    notes = models.TextField(blank=True)

    # Control de versiones para anulaciones
    is_active = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'electronic_invoices'
        ordering = ['-issue_date']

    def __str__(self):
        return f"FE {self.invoice_number} - {self.customer_name}"

    def generate_cude(self):
        """Generar CUDE según algoritmo DIAN"""
        # Algoritmo simplificado - en producción usar algoritmo oficial DIAN
        data = f"{self.invoice_number}{self.issue_date.strftime('%Y-%m-%d %H:%M:%S')}{self.total}{self.workshop_nit}"
        return hashlib.sha384(data.encode()).hexdigest()

    def validate_invoice_number(self):
        """Validar que el número de factura es válido según la resolución"""
        return self.dian_resolution.validate_invoice_number(self.invoice_number)

    def check_duplicate_invoice(self):
        """Verificar que el número no haya sido usado anteriormente"""
        return ElectronicInvoice.objects.filter(
            workshop=self.workshop,
            invoice_number=self.invoice_number
        ).exclude(id=self.id).exists()

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generar número usando resolución DIAN
            self.invoice_number = self.dian_resolution.get_next_number()
            self.consecutive_number = self.dian_resolution.current_number

        if not self.cude:
            self.cude = self.generate_cude()

        super().save(*args, **kwargs)


class ElectronicInvoiceDetail(models.Model):
    """Detalles de facturas electrónicas"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    electronic_invoice = models.ForeignKey(ElectronicInvoice, on_delete=models.CASCADE, related_name='details')
    part = models.ForeignKey(Part, on_delete=models.SET_NULL, null=True, blank=True, related_name='electronic_invoice_details')

    # Información del producto/servicio
    description = models.TextField()
    part_number = models.CharField(max_length=100, blank=True)

    # Clasificación DIAN (UNSPSC)
    unspsc_code = models.CharField(max_length=20, blank=True)  # Código UNSPSC
    brand_name = models.CharField(max_length=100, blank=True)
    model_name = models.CharField(max_length=100, blank=True)

    # Cantidades y precios
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_code = models.CharField(max_length=10, default='NIU')  # Unidad de medida DIAN
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Cálculos automáticos
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=19.00)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'electronic_invoice_details'

    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}"

    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = (self.quantity * self.unit_price) - self.discount

        # Calcular IVA si aplica
        if self.tax_rate > 0:
            self.tax_amount = self.subtotal * (Decimal(str(self.tax_rate)) / 100)
        else:
            self.tax_amount = 0

        self.total = self.subtotal + self.tax_amount
        super().save(*args, **kwargs)


class DianValidationLog(models.Model):
    """Log de validaciones DIAN"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='dian_validation_logs')
    electronic_invoice = models.ForeignKey(ElectronicInvoice, on_delete=models.CASCADE, related_name='validation_logs')

    # Tipo de validación
    VALIDATION_TYPE_CHOICES = [
        ('xml_schema', 'Validación XML Schema'),
        ('schematron', 'Validación Schematron'),
        ('dian_webservice', 'Validación DIAN WebService'),
        ('signature', 'Validación Firma Digital'),
    ]
    validation_type = models.CharField(max_length=20, choices=VALIDATION_TYPE_CHOICES)

    # Resultado
    is_valid = models.BooleanField()
    error_code = models.CharField(max_length=20, blank=True)
    error_message = models.TextField(blank=True)
    validation_details = models.JSONField(blank=True)  # Detalles adicionales en JSON

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'dian_validation_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.validation_type} - {self.electronic_invoice.invoice_number} - {'Válido' if self.is_valid else 'Inválido'}"


class WorkOrderItem(models.Model):
    """Ítems individuales de las órdenes de trabajo (servicios y repuestos)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='details')

    # Tipo de ítem
    ITEM_TYPE_CHOICES = [
        ('service', 'Servicio'),
        ('part', 'Repuesto'),
        ('labor', 'Mano de Obra'),
        ('other', 'Otro'),
    ]
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES, default='service')

    # Relaciones opcionales
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_order_items')
    part = models.ForeignKey(SparePart, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_order_items')

    # Información del ítem
    description = models.TextField(help_text="Descripción detallada del ítem")
    part_number = models.CharField(max_length=100, blank=True, help_text="Número de parte o código")

    # Cantidades y precios
    service_quantity = models.DecimalField(max_digits=6, decimal_places=2, default=1, help_text="Cantidad de servicios (horas)")
    part_quantity = models.IntegerField(default=1, help_text="Cantidad de repuestos")

    # Precios unitarios
    service_unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Precio por hora de servicio")
    part_unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Precio unitario del repuesto")

    # Costos calculados
    labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Costo total de mano de obra")
    parts_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Costo total de repuestos")
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Costo total del ítem")

    # Información adicional
    estimated_time_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0, help_text="Tiempo estimado en horas")
    actual_time_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0, help_text="Tiempo real en horas")

    # Estado del ítem
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    # Notas y observaciones
    notes = models.TextField(blank=True, help_text="Notas adicionales del ítem")

    # Control de inventario
    inventory_updated = models.BooleanField(default=False, help_text="Si el inventario ya fue actualizado")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'work_order_items'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_item_type_display()}: {self.description[:50]}"

    def save(self, *args, **kwargs):
        # Calcular costos automáticamente
        self.labor_cost = self.service_quantity * self.service_unit_price
        self.parts_cost = self.part_quantity * self.part_unit_price
        self.total_cost = self.labor_cost + self.parts_cost

        # Si es un repuesto, verificar stock disponible
        if self.part and self.part_quantity > 0:
            if self.part.stock_quantity < self.part_quantity:
                raise ValueError(f"Stock insuficiente para {self.part.name}. Disponible: {self.part.stock_quantity}")

        super().save(*args, **kwargs)

    def complete_item(self):
        """Marcar ítem como completado y actualizar inventario"""
        if self.status != 'completed':
            self.status = 'completed'

            # Actualizar inventario si es un repuesto
            if self.part and not self.inventory_updated:
                if self.part.stock_quantity >= self.part_quantity:
                    self.part.stock_quantity -= self.part_quantity
                    self.part.times_used += 1
                    self.part.last_sale_date = timezone.now().date()
                    self.part.save()
                    self.inventory_updated = True
                else:
                    raise ValueError(f"Stock insuficiente para {self.part.name}. Disponible: {self.part.stock_quantity}")

            # Actualizar estadísticas del servicio
            if self.service:
                self.service.update_statistics(
                    rating=None,  # Se puede agregar rating después
                    revenue=self.labor_cost
                )

            # Actualizar tiempo real si no está establecido
            if self.actual_time_hours == 0 and self.estimated_time_hours > 0:
                self.actual_time_hours = self.estimated_time_hours

            self.save()

            # Actualizar costos de la orden de trabajo
            self.work_order.update_costs()

    @property
    def is_service(self):
        """Verificar si es un ítem de servicio"""
        return self.item_type in ['service', 'labor']

    @property
    def is_part(self):
        """Verificar si es un ítem de repuesto"""
        return self.item_type == 'part'

    @property
    def progress_percentage(self):
        """Porcentaje de progreso del ítem"""
        status_progress = {
            'pending': 0,
            'in_progress': 50,
            'completed': 100,
            'cancelled': 0,
        }
        return status_progress.get(self.status, 0)


# Mantener compatibilidad - WorkOrderDetail ahora es WorkOrderItem
class Quotation(models.Model):
    """Cotizaciones para servicios de taller"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='quotations')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='quotations')

    # Numeración automática
    quotation_number = models.CharField(max_length=20, unique=True, editable=False)

    # Información básica
    title = models.CharField(max_length=200, help_text="Título de la cotización")
    description = models.TextField(blank=True, help_text="Descripción general de los trabajos")

    # Estados de la cotización
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('sent', 'Enviada'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
        ('expired', 'Expirada'),
        ('converted', 'Convertida a OT'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')

    # Fechas importantes
    created_date = models.DateTimeField(default=timezone.now)
    sent_date = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True, help_text="Fecha de expiración")
    approved_date = models.DateTimeField(null=True, blank=True)

    # Estimaciones globales
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    estimated_labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estimated_parts_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estimated_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Descuentos y ajustes
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Descuento en porcentaje")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Descuento en valor absoluto")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Valor de IVA")
    final_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total final con descuentos e IVA")

    # Información adicional
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    terms_conditions = models.TextField(blank=True, help_text="Términos y condiciones")

    # Conversión a orden de trabajo
    converted_to_work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_quotation'
    )

    # Estadísticas
    times_viewed = models.IntegerField(default=0)
    last_viewed_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quotations'
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['workshop', 'status']),
            models.Index(fields=['customer', 'created_date']),
            models.Index(fields=['valid_until', 'status']),
        ]

    def __str__(self):
        return f"COT-{self.quotation_number} - {self.customer.first_name} {self.customer.last_name}"

    def save(self, *args, **kwargs):
        if not self.quotation_number:
            # Generar número de cotización automático
            today = timezone.now().date()
            workshop_prefix = str(self.workshop.id)[:4].upper()
            # Contar cotizaciones del día para este taller
            daily_count = Quotation.objects.filter(
                workshop=self.workshop,
                created_date__date=today
            ).count() + 1
            self.quotation_number = f"COT{workshop_prefix}-{today.strftime('%Y%m%d')}-{daily_count:03d}"

        # Calcular totales automáticamente
        self.calculate_totals()

        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calcular totales desde los items de cotización"""
        from django.db.models import Sum

        # Calcular sumas desde QuotationItem
        totals = self.items.aggregate(
            total_labor=Sum('labor_cost', default=0),
            total_parts=Sum('parts_cost', default=0),
            total_hours=Sum('estimated_hours', default=0)
        )

        self.estimated_labor_cost = totals['total_labor'] or 0
        self.estimated_parts_cost = totals['total_parts'] or 0
        self.estimated_hours = totals['total_hours'] or 0
        self.estimated_total = self.estimated_labor_cost + self.estimated_parts_cost

        # Aplicar descuentos
        discount_from_percentage = self.estimated_total * (self.discount_percentage / 100)
        total_discount = discount_from_percentage + self.discount_amount
        subtotal_after_discount = self.estimated_total - total_discount

        # Calcular IVA (19% en Colombia)
        self.tax_amount = subtotal_after_discount * 0.19
        self.final_total = subtotal_after_discount + self.tax_amount

    @property
    def is_expired(self):
        """Verificar si la cotización ha expirado"""
        if self.valid_until:
            return timezone.now().date() > self.valid_until
        return False

    @property
    def days_until_expiry(self):
        """Días restantes hasta expiración"""
        if self.valid_until:
            today = timezone.now().date()
            if self.valid_until >= today:
                return (self.valid_until - today).days
            else:
                return -((today - self.valid_until).days)
        return None

    @property
    def acceptance_rate(self):
        """Tasa de aceptación (simulada - en producción calcular estadísticas)"""
        # En producción, calcular basado en historial del taller
        return 0.75  # 75% tasa de aceptación promedio

    def mark_as_sent(self):
        """Marcar cotización como enviada"""
        if self.status == 'draft':
            self.status = 'sent'
            self.sent_date = timezone.now()
            self.save()

    def approve(self):
        """Aprobar la cotización"""
        if self.status in ['draft', 'sent']:
            self.status = 'approved'
            self.approved_date = timezone.now()
            self.save()

    def reject(self):
        """Rechazar la cotización"""
        if self.status in ['draft', 'sent']:
            self.status = 'rejected'
            self.save()

    def convert_to_work_order(self, assigned_mechanic=None):
        """Convertir cotización aprobada en orden de trabajo"""
        if self.status != 'approved':
            raise ValueError("Solo se pueden convertir cotizaciones aprobadas")

        if self.converted_to_work_order:
            raise ValueError("Esta cotización ya fue convertida a orden de trabajo")

        # Crear orden de trabajo
        work_order = WorkOrder.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            vehicle=self.vehicle,
            assigned_mechanic=assigned_mechanic,
            title=f"OT generada desde {self.quotation_number}",
            description=self.description,
            estimated_hours=self.estimated_hours,
            estimated_cost=self.estimated_total,
            final_cost=self.final_total,
            status='approved'  # Iniciar como aprobada
        )

        # Copiar items de cotización a items de OT
        for quote_item in self.items.all():
            WorkOrderItem.objects.create(
                work_order=work_order,
                item_type=quote_item.item_type,
                service=quote_item.service,
                part=quote_item.part,
                description=quote_item.description,
                service_quantity=quote_item.service_quantity,
                part_quantity=quote_item.part_quantity,
                service_unit_price=quote_item.service_unit_price,
                part_unit_price=quote_item.part_unit_price,
                estimated_time_hours=quote_item.estimated_hours,
                status='pending'
            )

        # Actualizar cotización
        self.converted_to_work_order = work_order
        self.status = 'converted'
        self.save()

        return work_order


class QuotationItem(models.Model):
    """Items individuales de las cotizaciones"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')

    # Tipo de ítem
    ITEM_TYPE_CHOICES = [
        ('service', 'Servicio'),
        ('part', 'Repuesto'),
        ('labor', 'Mano de Obra'),
        ('other', 'Otro'),
    ]
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES, default='service')

    # Relaciones opcionales
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotation_items')
    part = models.ForeignKey(SparePart, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotation_items')

    # Información del ítem
    description = models.TextField(help_text="Descripción detallada del ítem")

    # Cantidades y precios
    service_quantity = models.DecimalField(max_digits=6, decimal_places=2, default=1, help_text="Cantidad de servicios (horas)")
    part_quantity = models.IntegerField(default=1, help_text="Cantidad de repuestos")

    # Precios unitarios
    service_unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Precio por hora de servicio")
    part_unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Precio unitario del repuesto")

    # Costos calculados
    labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Costo total de mano de obra")
    parts_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Costo total de repuestos")
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Costo total del ítem")

    # Estimaciones
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0, help_text="Tiempo estimado en horas")

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'quotation_items'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_item_type_display()}: {self.description[:50]}"

    def save(self, *args, **kwargs):
        # Calcular costos automáticamente
        self.labor_cost = self.service_quantity * self.service_unit_price
        self.parts_cost = self.part_quantity * self.part_unit_price
        self.total_cost = self.labor_cost + self.parts_cost
        super().save(*args, **kwargs)


class WorkOrderDetail(WorkOrderItem):
    """Alias para compatibilidad hacia atrás"""
    class Meta:
        proxy = True


class ServiceType(models.Model):
    """Tipos de servicios disponibles para agendamiento"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='service_types')

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=[
        ('maintenance', 'Mantenimiento'),
        ('repair', 'Reparación'),
        ('diagnostic', 'Diagnóstico'),
        ('emergency', 'Emergencia'),
        ('inspection', 'Inspección'),
        ('other', 'Otro'),
    ], default='maintenance')

    # Duración estimada en minutos
    estimated_duration = models.IntegerField(default=60, help_text="Duración estimada en minutos")

    # Precio base
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Color para visualización en calendario
    color = models.CharField(max_length=7, default='#3b82f6', help_text="Color en formato hex (#RRGGBB)")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'service_types'
        unique_together = ['workshop', 'name']
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Appointment(models.Model):
    """Citas del taller con funcionalidad completa de agenda"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='appointments')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='appointments')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='appointments', null=True, blank=True)
    assigned_mechanic = models.ForeignKey(Mechanic, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')

    # Información del servicio
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    custom_service_description = models.CharField(max_length=255, blank=True, help_text="Descripción si no es un tipo de servicio estándar")

    # Fechas y horarios
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Duración calculada automáticamente
    duration_minutes = models.IntegerField(default=60, help_text="Duración en minutos")

    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('confirmed', 'Confirmada'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('no_show', 'No Asistió'),
        ('cancelled', 'Cancelada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Información adicional
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ], default='normal')

    # Costos estimados
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Información de contacto y seguimiento
    contact_phone = models.CharField(max_length=20, blank=True, help_text="Teléfono de contacto alternativo")
    contact_email = models.EmailField(blank=True, help_text="Email de contacto alternativo")

    # Recordatorios
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    # Notas y observaciones
    notes = models.TextField(blank=True, help_text="Notas internas del taller")
    customer_notes = models.TextField(blank=True, help_text="Notas para el cliente")

    # Conversión a orden de trabajo
    converted_to_work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_appointment'
    )

    # Control de creación y actualización
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_appointments')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appointments'
        ordering = ['appointment_date', 'start_time']
        indexes = [
            models.Index(fields=['workshop', 'appointment_date']),
            models.Index(fields=['assigned_mechanic', 'appointment_date']),
            models.Index(fields=['customer', 'appointment_date']),
            models.Index(fields=['status', 'appointment_date']),
        ]

    def __str__(self):
        service = self.service_type.name if self.service_type else self.custom_service_description or "Servicio"
        return f"{self.customer.full_name} - {service} - {self.appointment_date} {self.start_time}"

    def save(self, *args, **kwargs):
        # Calcular duración automáticamente si no está establecida
        if not self.duration_minutes and self.start_time and self.end_time:
            start_minutes = self.start_time.hour * 60 + self.start_time.minute
            end_minutes = self.end_time.hour * 60 + self.end_time.minute
            self.duration_minutes = end_minutes - start_minutes

        # Calcular costo estimado si hay tipo de servicio
        if self.service_type and not self.estimated_cost:
            self.estimated_cost = self.service_type.base_price

        super().save(*args, **kwargs)

    @property
    def is_past(self):
        """Verificar si la cita ya pasó"""
        now = timezone.now()
        appointment_datetime = timezone.datetime.combine(self.appointment_date, self.start_time)
        appointment_datetime = timezone.make_aware(appointment_datetime)
        return now > appointment_datetime

    @property
    def is_today(self):
        """Verificar si la cita es para hoy"""
        return self.appointment_date == timezone.now().date()

    @property
    def is_upcoming(self):
        """Verificar si la cita está próxima (próximas 24 horas)"""
        now = timezone.now()
        appointment_datetime = timezone.datetime.combine(self.appointment_date, self.start_time)
        appointment_datetime = timezone.make_aware(appointment_datetime)
        time_diff = appointment_datetime - now
        return time_diff.total_seconds() > 0 and time_diff.total_seconds() <= 86400  # 24 horas

    @property
    def needs_reminder(self):
        """Verificar si necesita recordatorio (24 horas antes)"""
        if self.reminder_sent or self.status in ['completed', 'cancelled', 'no_show']:
            return False
        return self.is_upcoming

    @property
    def display_title(self):
        """Título para mostrar en calendario"""
        service = self.service_type.name if self.service_type else self.custom_service_description or "Servicio"
        return f"{self.customer.first_name} - {service}"

    @property
    def status_color(self):
        """Color CSS según estado"""
        colors = {
            'scheduled': '#f59e0b',    # amber
            'confirmed': '#3b82f6',   # blue
            'in_progress': '#f97316', # orange
            'completed': '#22c55e',   # green
            'no_show': '#ef4444',     # red
            'cancelled': '#6b7280',   # gray
        }
        return colors.get(self.status, '#6b7280')

    def send_reminder(self):
        """Marcar recordatorio como enviado"""
        self.reminder_sent = True
        self.reminder_sent_at = timezone.now()
        self.save()

    def convert_to_work_order(self, notes=None):
        """Convertir cita confirmada en orden de trabajo"""
        if self.status not in ['confirmed', 'in_progress']:
            raise ValueError("Solo se pueden convertir citas confirmadas o en progreso")

        if self.converted_to_work_order:
            raise ValueError("Esta cita ya fue convertida a orden de trabajo")

        # Crear orden de trabajo
        work_order = WorkOrder.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            vehicle=self.vehicle,
            assigned_mechanic=self.assigned_mechanic,
            title=f"OT generada desde cita: {self.display_title}",
            description=f"Cita programada para {self.appointment_date} a las {self.start_time}",
            estimated_hours=self.duration_minutes / 60,  # Convertir minutos a horas
            estimated_cost=self.estimated_cost,
            status='approved'  # Iniciar como aprobada
        )

        # Agregar servicio si existe
        if self.service_type:
            WorkOrderItem.objects.create(
                work_order=work_order,
                item_type='service',
                service=self.service_type,  # Asumiendo que ServiceType es compatible con Service
                description=self.service_type.description,
                service_quantity=self.duration_minutes / 60,
                service_unit_price=self.service_type.base_price / (self.duration_minutes / 60) if self.duration_minutes > 0 else 0,
                estimated_time_hours=self.duration_minutes / 60,
                status='pending'
            )

        # Actualizar cita
        self.converted_to_work_order = work_order
        self.status = 'completed'
        self.save()

        return work_order


class Invoice(models.Model):
    """Facturas del taller"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='invoices')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    work_order = models.OneToOneField(WorkOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice')

    # Numeración
    invoice_number = models.CharField(max_length=20, unique=True)
    consecutive_number = models.IntegerField()  # Número correlativo por taller

    # Fechas
    issue_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)

    # Información fiscal del taller
    workshop_nit = models.CharField(max_length=20)
    workshop_name = models.CharField(max_length=255)
    workshop_address = models.TextField()
    workshop_phone = models.CharField(max_length=20, blank=True)
    workshop_email = models.EmailField(blank=True)

    # Información del cliente
    customer_name = models.CharField(max_length=255)
    customer_document = models.CharField(max_length=20, blank=True)
    customer_address = models.TextField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)

    # Totales
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=19.00)  # IVA Colombia
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Estado y pagos
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Pagada'),
        ('overdue', 'Vencida'),
        ('cancelled', 'Cancelada'),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Efectivo'),
        ('card', 'Tarjeta'),
        ('transfer', 'Transferencia'),
        ('check', 'Cheque'),
        ('other', 'Otro'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)

    # Notas y observaciones
    notes = models.TextField(blank=True)

    # Control de versiones para anulaciones
    is_active = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-issue_date']

    def __str__(self):
        return f"Factura {self.invoice_number} - {self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generar número de factura automático
            today = timezone.now().date()
            workshop_prefix = str(self.workshop.id)[:4].upper()
            # Obtener el último número correlativo para este taller
            last_invoice = Invoice.objects.filter(workshop=self.workshop).order_by('-consecutive_number').first()
            next_number = (last_invoice.consecutive_number + 1) if last_invoice else 1
            self.consecutive_number = next_number
            self.invoice_number = f"F{workshop_prefix}-{today.strftime('%Y%m%d')}-{next_number:04d}"
        super().save(*args, **kwargs)


class InvoiceDetail(models.Model):
    """Detalles de las facturas (productos/servicios)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='details')
    part = models.ForeignKey(Part, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_details')

    # Descripción del producto/servicio
    description = models.TextField()
    part_number = models.CharField(max_length=100, blank=True)  # Para referencia

    # Cantidades y precios
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Cálculos automáticos
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'invoice_details'

    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}"

    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = (self.quantity * self.unit_price) - self.discount

        # Calcular IVA si aplica (19% en Colombia)
        if self.invoice.tax_rate > 0:
            self.tax_amount = self.subtotal * (self.invoice.tax_rate / 100)
        else:
            self.tax_amount = 0

        self.total = self.subtotal + self.tax_amount
        super().save(*args, **kwargs)


class CreditNote(models.Model):
    """Notas de crédito (devoluciones, descuentos)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='credit_notes')
    original_invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='credit_notes')

    # Numeración
    credit_note_number = models.CharField(max_length=20, unique=True)
    consecutive_number = models.IntegerField()

    # Información del cliente (misma que la factura original)
    customer_name = models.CharField(max_length=255)
    customer_document = models.CharField(max_length=20, blank=True)

    # Motivo de la nota de crédito
    CREDIT_REASON_CHOICES = [
        ('devolucion', 'Devolución de producto'),
        ('descuento', 'Descuento aplicado'),
        ('error_factura', 'Error en facturación'),
        ('cambio', 'Cambio de producto'),
        ('garantia', 'Producto en garantía'),
        ('other', 'Otro'),
    ]
    reason = models.CharField(max_length=20, choices=CREDIT_REASON_CHOICES)
    reason_description = models.TextField(blank=True)

    # Totales
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    issue_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'credit_notes'

    def __str__(self):
        return f"NC {self.credit_note_number} - {self.original_invoice.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.credit_note_number:
            # Generar número de nota de crédito automático
            today = timezone.now().date()
            workshop_prefix = str(self.workshop.id)[:4].upper()
            last_note = CreditNote.objects.filter(workshop=self.workshop).order_by('-consecutive_number').first()
            next_number = (last_note.consecutive_number + 1) if last_note else 1
            self.consecutive_number = next_number
            self.credit_note_number = f"NC{workshop_prefix}-{today.strftime('%Y%m%d')}-{next_number:04d}"
        super().save(*args, **kwargs)


class DebitNote(models.Model):
    """Notas de débito (cargos adicionales)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='debit_notes')
    original_invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='debit_notes')

    # Numeración
    debit_note_number = models.CharField(max_length=20, unique=True)
    consecutive_number = models.IntegerField()

    # Información del cliente
    customer_name = models.CharField(max_length=255)
    customer_document = models.CharField(max_length=20, blank=True)

    # Motivo de la nota de débito
    DEBIT_REASON_CHOICES = [
        ('cargo_adicional', 'Cargo adicional'),
        ('intereses', 'Intereses por mora'),
        ('cambio_precio', 'Cambio de precio'),
        ('servicio_extra', 'Servicio adicional'),
        ('error_factura', 'Corrección de error'),
        ('other', 'Otro'),
    ]
    reason = models.CharField(max_length=20, choices=DEBIT_REASON_CHOICES)
    reason_description = models.TextField(blank=True)

    # Totales
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    issue_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'debit_notes'

    def __str__(self):
        return f"ND {self.debit_note_number} - {self.original_invoice.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.debit_note_number:
            # Generar número de nota de débito automático
            today = timezone.now().date()
            workshop_prefix = str(self.workshop.id)[:4].upper()
            last_note = DebitNote.objects.filter(workshop=self.workshop).order_by('-consecutive_number').first()
            next_number = (last_note.consecutive_number + 1) if last_note else 1
            self.consecutive_number = next_number
            self.debit_note_number = f"ND{workshop_prefix}-{today.strftime('%Y%m%d')}-{next_number:04d}"
        super().save(*args, **kwargs)

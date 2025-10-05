from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"


class Workshop(models.Model):
    """Información del taller"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='workshop')
    name = models.CharField(max_length=255)
    nit = models.CharField(max_length=20, unique=True, blank=True, null=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
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
        return self.subscription_expires > timezone.now().date() and self.is_active


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

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    document_number = models.CharField(max_length=20, blank=True)

    total_visits = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'customers'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Motorcycle(models.Model):
    """Motos de los clientes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='motorcycles')
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='motorcycles')

    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    license_plate = models.CharField(max_length=10, blank=True)
    mileage = models.IntegerField(default=0)
    color = models.CharField(max_length=50, blank=True)

    FUEL_CHOICES = [
        ('gasolina', 'Gasolina'),
        ('electrico', 'Eléctrico'),
        ('hibrido', 'Híbrido'),
    ]
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='gasolina')

    TRANSMISSION_CHOICES = [
        ('manual', 'Manual'),
        ('automatico', 'Automático'),
    ]
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, default='manual')

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'motorcycles'

    def __str__(self):
        return f"{self.brand} {self.model} {self.year} - {self.license_plate}"


class Part(models.Model):
    """Repuestos del taller"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='parts')

    name = models.CharField(max_length=255)
    part_number = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    stock_quantity = models.IntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'parts'

    def __str__(self):
        return f"{self.name} - Stock: {self.stock_quantity}"


class WorkOrder(models.Model):
    """Órdenes de trabajo"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='work_orders')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='work_orders')
    motorcycle = models.ForeignKey(Motorcycle, on_delete=models.CASCADE, related_name='work_orders')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='work_orders')

    order_number = models.CharField(max_length=20, unique=True)

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    description = models.TextField(blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'work_orders'

    def __str__(self):
        return f"OT-{self.order_number} - {self.customer} - {self.motorcycle}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generar número de orden automático
            today = timezone.now().date()
            workshop_prefix = str(self.workshop.id)[:4].upper()
            self.order_number = f"{workshop_prefix}-{today.strftime('%Y%m%d')}-{WorkOrder.objects.filter(workshop=self.workshop, created_at__date=today).count() + 1:03d}"
        super().save(*args, **kwargs)


class WorkOrderDetail(models.Model):
    """Detalles de las órdenes de trabajo (servicios y repuestos)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='details')
    part = models.ForeignKey(Part, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_order_details')

    service_description = models.TextField(blank=True)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'work_order_details'

    @property
    def total_price(self):
        return self.quantity * self.unit_price


class Appointment(models.Model):
    """Citas del taller"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='appointments')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='appointments')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='appointments')

    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    service_type = models.CharField(max_length=100, blank=True)

    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('confirmed', 'Confirmada'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'appointments'
        ordering = ['appointment_date', 'start_time']

    def __str__(self):
        return f"{self.customer} - {self.appointment_date} {self.start_time}"

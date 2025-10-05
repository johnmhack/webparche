from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
import uuid


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

    # Información básica
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    part_number = models.CharField(max_length=100, blank=True, unique=True)

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

    # Inventario y precios
    stock_quantity = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=5)  # Nivel mínimo de stock
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Información adicional
    location = models.CharField(max_length=100, blank=True)  # Ubicación en el taller
    supplier = models.CharField(max_length=100, blank=True)
    warranty_months = models.IntegerField(default=0)

    # Estado
    is_active = models.BooleanField(default=True)
    is_taxable = models.BooleanField(default=True)  # Si aplica IVA

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'parts'
        unique_together = ['workshop', 'part_number']  # Un número de parte único por taller

    def __str__(self):
        return f"{self.name} - {self.part_number} - Stock: {self.stock_quantity}"

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
    def stock_value(self):
        """Valor total del stock"""
        return self.stock_quantity * self.unit_cost


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

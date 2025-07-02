from django.db import models

# Define aquí tus modelos (tablas) principales. 

class Negocio(models.Model):
    TIPO_CHOICES = [
        ('taller', 'Taller con almacén'),
        ('almacen', 'Solo almacén de repuestos'),
    ]
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    correo = models.EmailField(blank=True)
    nit = models.CharField(max_length=20, blank=True)
    # Puedes agregar más campos según lo necesites

    def __str__(self):
        return self.nombre

class Empleado(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    correo = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    documento = models.CharField(max_length=30, blank=True)
    fecha_ingreso = models.DateField()

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.negocio.nombre})"

class Inventario(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    marca = models.CharField(max_length=100, blank=True)
    tamano = models.CharField(max_length=50, blank=True)
    categoria = models.CharField(max_length=100, blank=True)
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    codigo = models.CharField(max_length=50, blank=True)
    ubicacion = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.negocio.nombre})"

class Servicio(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    # Solo los negocios de tipo "taller" deberían tener servicios

    def __str__(self):
        return f"{self.nombre} ({self.negocio.nombre})"

class Cliente(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    documento = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.negocio.nombre})"

class Vehiculo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    placa = models.CharField(max_length=20)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.PositiveIntegerField()
    color = models.CharField(max_length=30, blank=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo} ({self.cliente.nombre} {self.cliente.apellido})"

class OrdenDeServicio(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('finalizado', 'Finalizado'),
    ]
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    fecha_ingreso = models.DateField()
    fecha_salida = models.DateField(blank=True, null=True)
    servicios = models.ManyToManyField(Servicio, blank=True)
    observaciones = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    def __str__(self):
        return f"Orden #{self.id} - {self.vehiculo.placa} ({self.cliente.nombre} {self.cliente.apellido})"

class Factura(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    orden_de_servicio = models.ForeignKey(OrdenDeServicio, on_delete=models.CASCADE)
    fecha = models.DateField()
    total = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=50)
    observaciones = models.TextField(blank=True)
    numero_factura = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Factura #{self.numero_factura or self.id} - {self.negocio.nombre}"

class FacturaItem(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='items')
    descripcion = models.CharField(max_length=200)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    servicio = models.ForeignKey(Servicio, on_delete=models.SET_NULL, null=True, blank=True)
    producto = models.ForeignKey(Inventario, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.descripcion} x{self.cantidad} (Factura #{self.factura.numero_factura or self.factura.id})" 
from django.contrib import admin
from .models import Negocio, Inventario, Servicio, Empleado, Cliente, Vehiculo, OrdenDeServicio, Factura, FacturaItem

class InventarioInline(admin.TabularInline):
    model = Inventario
    extra = 1  # Muestra un formulario vacío adicional

class FacturaItemInline(admin.TabularInline):
    model = FacturaItem
    extra = 1

class NegocioAdmin(admin.ModelAdmin):
    inlines = [InventarioInline]

class FacturaAdmin(admin.ModelAdmin):
    inlines = [FacturaItemInline]

admin.site.register(Negocio, NegocioAdmin)
admin.site.register(Inventario)
admin.site.register(Servicio)
admin.site.register(Empleado)
admin.site.register(Cliente)
admin.site.register(Vehiculo)
admin.site.register(OrdenDeServicio)
admin.site.register(Factura, FacturaAdmin)
admin.site.register(FacturaItem)

# Registra tus modelos aquí. 
from rest_framework import serializers
from .models import (
    User, Workshop, Customer, Vehicle, Mechanic,
    Service, SparePart, WorkOrder, WorkOrderItem, WorkOrderStatusLog,
    Quotation, QuotationItem, Appointment, ServiceType,
    Invoice, InvoiceDetail, CreditNote, DebitNote,
    ElectronicInvoice, ElectronicInvoiceDetail, DianResolution
)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'password']

    def create(self, validated_data):
        # Para el modelo User personalizado, username es el email
        validated_data['username'] = validated_data['email']
        user = User.objects.create_user(**validated_data)
        return user


class WorkshopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workshop
        fields = '__all__'
        read_only_fields = ['owner']


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['workshop']


class VehicleSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    customer_last_name = serializers.CharField(source='customer.last_name', read_only=True)

    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ['workshop']


class MechanicSerializer(serializers.ModelSerializer):
    performance_score_display = serializers.SerializerMethodField()
    available_hours_today = serializers.SerializerMethodField()

    class Meta:
        model = Mechanic
        fields = '__all__'
        read_only_fields = ['workshop']

    def get_performance_score_display(self, obj):
        return f"{obj.performance_score:.1f}/100"

    def get_available_hours_today(self, obj):
        return obj.available_hours_today


class ServiceSerializer(serializers.ModelSerializer):
    estimated_cost_display = serializers.SerializerMethodField()
    is_popular_display = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = '__all__'
        read_only_fields = ['workshop']

    def get_estimated_cost_display(self, obj):
        return f"${obj.estimated_cost:,.0f}"

    def get_is_popular_display(self, obj):
        return "Popular" if obj.is_popular else "Regular"


class SparePartSerializer(serializers.ModelSerializer):
    profit_margin_display = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = SparePart
        fields = '__all__'
        read_only_fields = ['workshop']

    def get_profit_margin_display(self, obj):
        return f"{obj.profit_margin:.1f}%"

    def get_stock_status(self, obj):
        if obj.is_low_stock:
            return "Bajo"
        elif obj.is_overstock:
            return "Exceso"
        else:
            return "Normal"


# Mantener compatibilidad
class MotorcycleSerializer(VehicleSerializer):
    """Alias para compatibilidad hacia atrás"""
    pass

class EmployeeSerializer(MechanicSerializer):
    """Alias para compatibilidad hacia atrás"""
    pass

class PartSerializer(SparePartSerializer):
    """Alias para compatibilidad hacia atrás"""
    pass


class WorkOrderItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    part_name = serializers.CharField(source='part.name', read_only=True)
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = WorkOrderItem
        fields = '__all__'
        read_only_fields = ['labor_cost', 'parts_cost', 'total_cost']


class WorkOrderStatusLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.first_name', read_only=True)

    class Meta:
        model = WorkOrderStatusLog
        fields = '__all__'


class WorkOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    customer_full_name = serializers.SerializerMethodField()
    vehicle_info = serializers.SerializerMethodField()
    assigned_mechanic_name = serializers.CharField(source='assigned_mechanic.first_name', read_only=True)
    details = WorkOrderItemSerializer(many=True, read_only=True)
    status_logs = WorkOrderStatusLogSerializer(many=True, read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    total_cost = serializers.ReadOnlyField()

    class Meta:
        model = WorkOrder
        fields = '__all__'
        read_only_fields = ['workshop', 'order_number', 'labor_cost', 'parts_cost', 'total_services', 'total_parts']

    def get_customer_full_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"

    def get_vehicle_info(self, obj):
        return f"{obj.vehicle.brand} {obj.vehicle.model} {obj.vehicle.year}"


class QuotationItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    part_name = serializers.CharField(source='part.name', read_only=True)
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)

    class Meta:
        model = QuotationItem
        fields = '__all__'
        read_only_fields = ['labor_cost', 'parts_cost', 'total_cost']


class QuotationSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    customer_full_name = serializers.SerializerMethodField()
    vehicle_info = serializers.SerializerMethodField()
    items = QuotationItemSerializer(many=True, read_only=True)
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    final_total_display = serializers.SerializerMethodField()

    class Meta:
        model = Quotation
        fields = '__all__'
        read_only_fields = ['workshop', 'quotation_number', 'estimated_labor_cost', 'estimated_parts_cost',
                           'estimated_total', 'tax_amount', 'final_total']

    def get_customer_full_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"

    def get_vehicle_info(self, obj):
        return f"{obj.vehicle.brand} {obj.vehicle.model} {obj.vehicle.year}"

    def get_final_total_display(self, obj):
        return f"${obj.final_total:,.0f}"


# Mantener compatibilidad
class WorkOrderDetailSerializer(WorkOrderItemSerializer):
    """Alias para compatibilidad hacia atrás"""
    pass


class ServiceTypeSerializer(serializers.ModelSerializer):
    """Serializer para tipos de servicios de agenda"""
    estimated_duration_display = serializers.SerializerMethodField()

    class Meta:
        model = ServiceType
        fields = '__all__'
        read_only_fields = ['workshop']

    def get_estimated_duration_display(self, obj):
        hours = obj.estimated_duration // 60
        minutes = obj.estimated_duration % 60
        if hours > 0:
            return f"{hours}h {minutes}min"
        return f"{minutes}min"


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer completo para citas de agenda"""
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    customer_full_name = serializers.SerializerMethodField()
    vehicle_info = serializers.SerializerMethodField()
    assigned_mechanic_name = serializers.CharField(source='assigned_mechanic.first_name', read_only=True)
    service_type_name = serializers.CharField(source='service_type.name', read_only=True)
    display_title = serializers.ReadOnlyField()
    status_color = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    is_today = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    needs_reminder = serializers.ReadOnlyField()

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['workshop', 'duration_minutes', 'estimated_cost', 'created_by', 'updated_at']

    def get_customer_full_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"

    def get_vehicle_info(self, obj):
        if obj.vehicle:
            return f"{obj.vehicle.brand} {obj.vehicle.model} {obj.vehicle.year}"
        return "Sin vehículo especificado"


class InvoiceDetailSerializer(serializers.ModelSerializer):
    part_name = serializers.CharField(source='part.name', read_only=True)
    part_number = serializers.CharField(source='part.part_number', read_only=True)

    class Meta:
        model = InvoiceDetail
        fields = '__all__'
        read_only_fields = ['invoice', 'subtotal', 'tax_amount', 'total']


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    workshop_name = serializers.CharField(source='workshop.name', read_only=True)
    details = InvoiceDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['workshop', 'invoice_number', 'consecutive_number', 'subtotal', 'tax_amount', 'total']


class CreditNoteSerializer(serializers.ModelSerializer):
    original_invoice_number = serializers.CharField(source='original_invoice.invoice_number', read_only=True)
    workshop_name = serializers.CharField(source='workshop.name', read_only=True)

    class Meta:
        model = CreditNote
        fields = '__all__'
        read_only_fields = ['workshop', 'credit_note_number', 'consecutive_number']


class DebitNoteSerializer(serializers.ModelSerializer):
    original_invoice_number = serializers.CharField(source='original_invoice.invoice_number', read_only=True)
    workshop_name = serializers.CharField(source='workshop.name', read_only=True)

    class Meta:
        model = DebitNote
        fields = '__all__'
        read_only_fields = ['workshop', 'debit_note_number', 'consecutive_number']


# ===== SERIALIZERS PARA FACTURACIÓN ELECTRÓNICA DIAN =====

class DianResolutionSerializer(serializers.ModelSerializer):
    """Serializer para resoluciones DIAN"""
    days_until_expiry = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    usage_percentage = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()
    available_numbers = serializers.ReadOnlyField()
    resolution_status = serializers.SerializerMethodField()

    class Meta:
        model = DianResolution
        fields = '__all__'
        read_only_fields = ['workshop']

    def get_days_until_expiry(self, obj):
        return obj.days_until_expiry

    def get_is_expired(self, obj):
        return obj.is_expired

    def get_status_display(self, obj):
        return "Activa" if obj.is_active else "Inactiva"

    def get_resolution_status(self, obj):
        return obj.get_resolution_status()


class ElectronicInvoiceDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles de facturas electrónicas DIAN"""
    part_name = serializers.CharField(source='electronic_invoice.part.name', read_only=True)
    subtotal_display = serializers.SerializerMethodField()
    tax_amount_display = serializers.SerializerMethodField()
    total_display = serializers.SerializerMethodField()

    class Meta:
        model = ElectronicInvoiceDetail
        fields = '__all__'
        read_only_fields = ['electronic_invoice', 'subtotal', 'tax_amount', 'total']

    def get_subtotal_display(self, obj):
        return f"${obj.subtotal:,.2f}"

    def get_tax_amount_display(self, obj):
        return f"${obj.tax_amount:,.2f}"

    def get_total_display(self, obj):
        return f"${obj.total:,.2f}"


class ElectronicInvoiceSerializer(serializers.ModelSerializer):
    """Serializer para facturas electrónicas DIAN"""
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    workshop_name = serializers.CharField(source='workshop.name', read_only=True)
    dian_resolution_number = serializers.CharField(source='dian_resolution.resolution_number', read_only=True)
    details = ElectronicInvoiceDetailSerializer(many=True, read_only=True)
    dian_status_display = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()
    qr_code_image_url = serializers.SerializerMethodField()
    xml_download_url = serializers.SerializerMethodField()
    pdf_download_url = serializers.SerializerMethodField()

    class Meta:
        model = ElectronicInvoice
        fields = '__all__'
        read_only_fields = [
            'workshop', 'invoice_number', 'consecutive_number', 'cude',
            'xml_content', 'qr_code_url', 'qr_code_image', 'dian_status', 'dian_response_code',
            'dian_response_message', 'dian_response_date', 'subtotal',
            'tax_amount', 'total', 'issue_date'
        ]

    def get_dian_status_display(self, obj):
        status_map = {
            'draft': 'Borrador',
            'generated': 'XML Generado',
            'signed': 'Firmada',
            'sent': 'Enviada a DIAN',
            'processing': 'Procesando',
            'processed': 'Aprobada',
            'send_failed': 'Error de Envío',
            'rejected': 'Rechazada'
        }
        return status_map.get(obj.dian_status, 'Desconocido')

    def get_qr_code_url(self, obj):
        if obj.qr_code_url:
            return obj.qr_code_url
        return None

    def get_qr_code_image_url(self, obj):
        if obj.qr_code_image:
            return obj.qr_code_image.url
        return None

    def get_xml_download_url(self, obj):
        if obj.xml_content:
            return f"/api/electronic-invoices/{obj.id}/download_xml/"
        return None

    def get_pdf_download_url(self, obj):
        return f"/api/electronic-invoices/{obj.id}/download_pdf/"
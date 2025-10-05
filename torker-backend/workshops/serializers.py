from rest_framework import serializers
from .models import (
    User, Workshop, Customer, Motorcycle, Employee,
    Part, WorkOrder, WorkOrderDetail, Appointment,
    Invoice, InvoiceDetail, CreditNote, DebitNote
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


class MotorcycleSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)

    class Meta:
        model = Motorcycle
        fields = '__all__'
        read_only_fields = ['workshop']


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ['workshop']


class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = '__all__'
        read_only_fields = ['workshop']


class WorkOrderDetailSerializer(serializers.ModelSerializer):
    part_name = serializers.CharField(source='part.name', read_only=True)

    class Meta:
        model = WorkOrderDetail
        fields = '__all__'


class WorkOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    motorcycle_info = serializers.SerializerMethodField()
    details = WorkOrderDetailSerializer(many=True, read_only=True)

    class Meta:
        model = WorkOrder
        fields = '__all__'
        read_only_fields = ['workshop', 'order_number']

    def get_motorcycle_info(self, obj):
        return f"{obj.motorcycle.brand} {obj.motorcycle.model} {obj.motorcycle.year}"


class AppointmentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['workshop']


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
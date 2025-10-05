from rest_framework import serializers
from .models import (
    User, Workshop, Customer, Motorcycle, Employee,
    Part, WorkOrder, WorkOrderDetail, Appointment
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
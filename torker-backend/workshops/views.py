from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from .models import (
    User, Workshop, Customer, Motorcycle, Employee,
    Part, WorkOrder, WorkOrderDetail, Appointment
)
from .serializers import (
    UserSerializer, WorkshopSerializer, CustomerSerializer,
    MotorcycleSerializer, EmployeeSerializer, PartSerializer,
    WorkOrderSerializer, WorkOrderDetailSerializer, AppointmentSerializer
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Crear taller automáticamente
            Workshop.objects.create(
                owner=user,
                name=f"Taller de {user.first_name}",
                subscription_plan='trial'
            )
            return Response({
                'message': 'Usuario registrado exitosamente',
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            workshop = request.user.workshop
            return Response({
                'workshop': WorkshopSerializer(workshop).data,
                'stats': {
                    'customers': workshop.customers.count(),
                    'motorcycles': workshop.motorcycles.count(),
                    'work_orders': workshop.work_orders.count(),
                    'employees': workshop.employees.count(),
                }
            })
        except Workshop.DoesNotExist:
            return Response({
                'error': 'No se encontró el taller del usuario'
            }, status=status.HTTP_404_NOT_FOUND)


class WorkshopViewSet(viewsets.ModelViewSet):
    serializer_class = WorkshopSerializer
    permission_classes = [IsAuthenticated]
    queryset = Workshop.objects.all()

    def get_queryset(self):
        return Workshop.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    queryset = Customer.objects.all()

    def get_queryset(self):
        return Customer.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)


class MotorcycleViewSet(viewsets.ModelViewSet):
    serializer_class = MotorcycleSerializer
    permission_classes = [IsAuthenticated]
    queryset = Motorcycle.objects.all()

    def get_queryset(self):
        return Motorcycle.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)


class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    queryset = Employee.objects.all()

    def get_queryset(self):
        return Employee.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)


class PartViewSet(viewsets.ModelViewSet):
    serializer_class = PartSerializer
    permission_classes = [IsAuthenticated]
    queryset = Part.objects.all()

    def get_queryset(self):
        return Part.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)


class WorkOrderViewSet(viewsets.ModelViewSet):
    serializer_class = WorkOrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = WorkOrder.objects.all()

    def get_queryset(self):
        return WorkOrder.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    queryset = Appointment.objects.all()

    def get_queryset(self):
        return Appointment.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)


# TEMPORAL: Endpoint para crear usuario de prueba
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def create_test_user(request):
    """Endpoint temporal para crear usuario de prueba"""
    try:
        if User.objects.filter(email='test@example.com').exists():
            return Response({'message': 'Usuario ya existe'})

        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='test123',
            first_name='Usuario',
            last_name='Prueba'
        )

        workshop = Workshop.objects.create(
            name='Taller Demo',
            owner=user,
            email='test@example.com',
            phone='+573001234567'
        )

        return Response({
            'message': 'Usuario creado exitosamente',
            'email': 'test@example.com',
            'password': 'test123'
        })

    except Exception as e:
        return Response({'error': str(e)}, status=500)

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from django.http import HttpResponse
from .models import (
    User, Workshop, Customer, Motorcycle, Employee,
    Part, WorkOrder, WorkOrderDetail, Appointment,
    Invoice, InvoiceDetail, CreditNote, DebitNote
)
from .serializers import (
    UserSerializer, WorkshopSerializer, CustomerSerializer,
    MotorcycleSerializer, EmployeeSerializer, PartSerializer,
    WorkOrderSerializer, WorkOrderDetailSerializer, AppointmentSerializer,
    InvoiceSerializer, InvoiceDetailSerializer, CreditNoteSerializer, DebitNoteSerializer
)
from .pdf_generator import generate_invoice_pdf


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


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    queryset = Invoice.objects.all()

    def get_queryset(self):
        return Invoice.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        workshop = self.request.user.workshop
        serializer.save(workshop=workshop)

    @action(detail=False, methods=['post'])
    def create_from_work_order(self, request):
        """Crear factura desde una orden de trabajo completada"""
        work_order_id = request.data.get('work_order_id')
        payment_method = request.data.get('payment_method', 'cash')

        try:
            work_order = WorkOrder.objects.get(
                id=work_order_id,
                workshop=request.user.workshop,
                status='completed'
            )

            # Verificar que no existe factura para esta OT
            if hasattr(work_order, 'invoice'):
                return Response({'error': 'Ya existe una factura para esta orden de trabajo'},
                              status=status.HTTP_400_BAD_REQUEST)

            # Crear factura
            invoice = Invoice.objects.create(
                workshop=work_order.workshop,
                customer=work_order.customer,
                work_order=work_order,
                payment_method=payment_method,
                # Información fiscal del taller
                workshop_nit=work_order.workshop.nit or '',
                workshop_name=work_order.workshop.legal_name or work_order.workshop.name,
                workshop_address=work_order.workshop.address,
                workshop_phone=work_order.workshop.phone or '',
                workshop_email=work_order.workshop.email or '',
                # Información del cliente
                customer_name=work_order.customer.full_name,
                customer_document=f"{work_order.customer.get_document_type_display()} {work_order.customer.document_number}",
                customer_address=work_order.customer.full_address,
                customer_phone=work_order.customer.phone or '',
                customer_email=work_order.customer.email or '',
                # Configuración fiscal
                tax_rate=work_order.workshop.default_tax_rate,
            )

            # Crear detalles de factura desde la orden de trabajo
            subtotal = 0
            for detail in work_order.details.all():
                invoice_detail = InvoiceDetail.objects.create(
                    invoice=invoice,
                    part=detail.part,
                    description=detail.service_description or f"Repuesto: {detail.part.name if detail.part else 'Servicio'}",
                    quantity=detail.quantity,
                    unit_price=detail.unit_price,
                    discount=0,  # Por ahora sin descuento
                )
                subtotal += invoice_detail.subtotal

                # Descontar del inventario si es un repuesto
                if detail.part:
                    detail.part.stock_quantity -= detail.quantity
                    detail.part.save()

            # Calcular totales
            tax_amount = subtotal * (invoice.tax_rate / 100) if invoice.tax_rate > 0 else 0
            total = subtotal + tax_amount

            # Actualizar factura
            invoice.subtotal = subtotal
            invoice.tax_amount = tax_amount
            invoice.total = total
            invoice.save()

            # Actualizar estadísticas del cliente
            work_order.customer.total_spent += total
            work_order.customer.total_visits += 1
            work_order.customer.last_visit = invoice.issue_date
            work_order.customer.save()

            serializer = self.get_serializer(invoice)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except WorkOrder.DoesNotExist:
            return Response({'error': 'Orden de trabajo no encontrada o no completada'},
                          status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Descargar PDF de la factura"""
        try:
            invoice = self.get_object()

            # Verificar que la factura pertenece al taller del usuario
            if invoice.workshop != request.user.workshop:
                return Response({'error': 'No tienes permiso para acceder a esta factura'},
                              status=status.HTTP_403_FORBIDDEN)

            # Generar PDF
            pdf_data = generate_invoice_pdf(invoice.id)

            # Crear respuesta HTTP con el PDF
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="factura_{invoice.invoice_number}.pdf"'
            response['Content-Length'] = len(pdf_data)

            return response

        except Invoice.DoesNotExist:
            return Response({'error': 'Factura no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Error generando PDF: {str(e)}'},
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreditNoteViewSet(viewsets.ModelViewSet):
    serializer_class = CreditNoteSerializer
    permission_classes = [IsAuthenticated]
    queryset = CreditNote.objects.all()

    def get_queryset(self):
        return CreditNote.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        workshop = self.request.user.workshop
        serializer.save(workshop=workshop)


class DebitNoteViewSet(viewsets.ModelViewSet):
    serializer_class = DebitNoteSerializer
    permission_classes = [IsAuthenticated]
    queryset = DebitNote.objects.all()

    def get_queryset(self):
        return DebitNote.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        workshop = self.request.user.workshop
        serializer.save(workshop=workshop)

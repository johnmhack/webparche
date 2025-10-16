from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from django.http import HttpResponse
from .models import (
    User, Workshop, Customer, Vehicle, Mechanic,
    Service, SparePart, WorkOrder, WorkOrderItem, WorkOrderStatusLog,
    Quotation, QuotationItem, Appointment,
    Invoice, InvoiceDetail, CreditNote, DebitNote,
    ElectronicInvoice, DianResolution
)
from .serializers import (
    UserSerializer, WorkshopSerializer, CustomerSerializer,
    VehicleSerializer, MechanicSerializer, ServiceSerializer, SparePartSerializer,
    WorkOrderSerializer, WorkOrderItemSerializer, WorkOrderStatusLogSerializer,
    QuotationSerializer, QuotationItemSerializer, AppointmentSerializer,
    InvoiceSerializer, InvoiceDetailSerializer, CreditNoteSerializer, DebitNoteSerializer,
    ElectronicInvoiceSerializer, DianResolutionSerializer
)
try:
    from .pdf_generator import generate_invoice_pdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    generate_invoice_pdf = None


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Extraer datos del taller
        workshop_name = request.data.get('workshopName', 'Mi Taller de Motos')

        # Crear datos del usuario sin workshopName
        user_data = request.data.copy()
        user_data.pop('workshopName', None)  # Remover workshopName para UserSerializer

        serializer = UserSerializer(data=user_data)
        if serializer.is_valid():
            user = serializer.save()
            # Crear taller con el nombre proporcionado
            Workshop.objects.create(
                owner=user,
                name=workshop_name,
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
                    'vehicles': workshop.vehicles.count(),
                    'work_orders': workshop.work_orders.count(),
                    'mechanics': workshop.mechanics.count(),
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


class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]
    queryset = Vehicle.objects.all()

    def get_queryset(self):
        return Vehicle.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)


class MechanicViewSet(viewsets.ModelViewSet):
    serializer_class = MechanicSerializer
    permission_classes = [IsAuthenticated]
    queryset = Mechanic.objects.all()

    def get_queryset(self):
        return Mechanic.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)

    @action(detail=True, methods=['get'])
    def performance_stats(self, request, pk=None):
        """Obtener estadísticas de rendimiento del mecánico"""
        mechanic = self.get_object()
        stats = mechanic.get_performance_stats()
        return Response(stats)


class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]
    queryset = Service.objects.all()

    def get_queryset(self):
        return Service.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Obtener servicios populares"""
        services = self.get_queryset().filter(is_popular=True)
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)


class SparePartViewSet(viewsets.ModelViewSet):
    serializer_class = SparePartSerializer
    permission_classes = [IsAuthenticated]
    queryset = SparePart.objects.all()

    def get_queryset(self):
        return SparePart.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Obtener repuestos con stock bajo"""
        parts = self.get_queryset().filter(is_low_stock=True)
        serializer = self.get_serializer(parts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Obtener repuestos agotados"""
        parts = self.get_queryset().filter(stock_quantity=0)
        serializer = self.get_serializer(parts, many=True)
        return Response(serializer.data)


# Mantener compatibilidad
class MotorcycleViewSet(VehicleViewSet):
    """Alias para compatibilidad hacia atrás"""
    pass

class EmployeeViewSet(MechanicViewSet):
    """Alias para compatibilidad hacia atrás"""
    pass

class PartViewSet(SparePartViewSet):
    """Alias para compatibilidad hacia atrás"""
    pass


class WorkOrderViewSet(viewsets.ModelViewSet):
    serializer_class = WorkOrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = WorkOrder.objects.all()

    def get_queryset(self):
        return WorkOrder.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Cambiar estado de la orden de trabajo"""
        work_order = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')

        if not new_status:
            return Response(
                {'error': 'Se requiere especificar el nuevo estado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            work_order.change_status(new_status, request.user, notes)
            serializer = self.get_serializer(work_order)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def assign_mechanic(self, request, pk=None):
        """Asignar mecánico a la orden de trabajo"""
        work_order = self.get_object()
        mechanic_id = request.data.get('mechanic_id')

        try:
            mechanic = Mechanic.objects.get(id=mechanic_id, workshop=work_order.workshop)
            work_order.assigned_mechanic = mechanic
            work_order.save()

            # Crear log de asignación
            WorkOrderStatusLog.objects.create(
                work_order=work_order,
                old_status=work_order.status,
                new_status=work_order.status,
                changed_by=request.user,
                notes=f"Mecánico asignado: {mechanic.first_name} {mechanic.last_name}"
            )

            serializer = self.get_serializer(work_order)
            return Response(serializer.data)
        except Mechanic.DoesNotExist:
            return Response({'error': 'Mecánico no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Obtener órdenes de trabajo atrasadas"""
        work_orders = self.get_queryset().filter(is_overdue=True)
        serializer = self.get_serializer(work_orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Obtener órdenes de trabajo por estado"""
        status_filter = request.query_params.get('status')
        if status_filter:
            work_orders = self.get_queryset().filter(status=status_filter)
        else:
            work_orders = self.get_queryset()
        serializer = self.get_serializer(work_orders, many=True)
        return Response(serializer.data)


class QuotationViewSet(viewsets.ModelViewSet):
    serializer_class = QuotationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Quotation.objects.all()

    def get_queryset(self):
        return Quotation.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)

    @action(detail=True, methods=['post'])
    def mark_as_sent(self, request, pk=None):
        """Marcar cotización como enviada"""
        quotation = self.get_object()
        quotation.mark_as_sent()
        serializer = self.get_serializer(quotation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Aprobar cotización"""
        quotation = self.get_object()
        try:
            quotation.approve()
            serializer = self.get_serializer(quotation)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rechazar cotización"""
        quotation = self.get_object()
        quotation.reject()
        serializer = self.get_serializer(quotation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def convert_to_work_order(self, request, pk=None):
        """Convertir cotización aprobada en orden de trabajo"""
        quotation = self.get_object()
        mechanic_id = request.data.get('mechanic_id')

        try:
            mechanic = None
            if mechanic_id:
                mechanic = Mechanic.objects.get(id=mechanic_id, workshop=quotation.workshop)

            work_order = quotation.convert_to_work_order(mechanic)
            work_order_serializer = WorkOrderSerializer(work_order)
            return Response(work_order_serializer.data, status=status.HTTP_201_CREATED)
        except Mechanic.DoesNotExist:
            return Response({'error': 'Mecánico no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Obtener cotizaciones expiradas"""
        quotations = self.get_queryset().filter(is_expired=True)
        serializer = self.get_serializer(quotations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        """Obtener cotizaciones pendientes de aprobación"""
        quotations = self.get_queryset().filter(status='sent')
        serializer = self.get_serializer(quotations, many=True)
        return Response(serializer.data)


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
            name='Mi Taller de Motos',
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

            # Crear detalles de factura desde los ítems de la orden de trabajo
            subtotal = 0
            for item in work_order.details.all():
                # Usar la descripción del ítem o generar una apropiada
                description = item.description
                if not description:
                    if item.service:
                        description = f"Servicio: {item.service.name}"
                    elif item.part:
                        description = f"Repuesto: {item.part.name}"
                    else:
                        description = "Ítem de orden de trabajo"

                invoice_detail = InvoiceDetail.objects.create(
                    invoice=invoice,
                    part=item.part,
                    description=description,
                    quantity=item.part_quantity if item.part_quantity > 0 else item.service_quantity,
                    unit_price=item.part_unit_price if item.part_unit_price > 0 else item.service_unit_price,
                    discount=0,  # Por ahora sin descuento
                )
                subtotal += invoice_detail.subtotal

                # Descontar del inventario si es un repuesto (ya se hizo en complete_item)
                # Solo actualizar estadísticas del repuesto
                if item.part and item.inventory_updated:
                    item.part.times_used += 1
                    item.part.last_sale_date = invoice.issue_date.date()
                    item.part.save()

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

            # Cambiar estado de la OT a facturada
            work_order.change_status('invoiced', request.user, f'Facturada con {invoice.invoice_number}')

            serializer = self.get_serializer(invoice)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except WorkOrder.DoesNotExist:
            return Response({'error': 'Orden de trabajo no encontrada o no completada'},
                          status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def create_electronic_invoice_from_work_order(self, request):
        """Crear factura electrónica DIAN desde una orden de trabajo completada"""
        work_order_id = request.data.get('work_order_id')
        payment_method = request.data.get('payment_method', 'cash')

        try:
            work_order = WorkOrder.objects.get(
                id=work_order_id,
                workshop=request.user.workshop,
                status='completed'
            )

            # Verificar que no existe factura electrónica para esta OT
            if hasattr(work_order, 'electronic_invoice'):
                return Response({'error': 'Ya existe una factura electrónica para esta orden de trabajo'},
                              status=status.HTTP_400_BAD_REQUEST)

            # Verificar que el taller tenga resolución DIAN activa
            try:
                dian_resolution = DianResolution.objects.get(
                    workshop=work_order.workshop,
                    document_type='invoice',
                    is_active=True
                )
            except DianResolution.DoesNotExist:
                return Response({'error': 'No hay resolución DIAN activa para facturas electrónicas'},
                              status=status.HTTP_400_BAD_REQUEST)

            # Crear factura electrónica
            electronic_invoice = ElectronicInvoice.objects.create(
                workshop=work_order.workshop,
                customer=work_order.customer,
                work_order=work_order,
                dian_resolution=dian_resolution,
                payment_method=payment_method,
                # Información fiscal del taller
                workshop_nit=work_order.workshop.nit or '',
                workshop_name=work_order.workshop.legal_name or work_order.workshop.name,
                workshop_address=work_order.workshop.address,
                workshop_city=work_order.workshop.city or '',
                workshop_department=work_order.workshop.department or '',
                workshop_phone=work_order.workshop.phone or '',
                workshop_email=work_order.workshop.email or '',
                # Información del cliente
                customer_name=work_order.customer.full_name,
                customer_document_type=work_order.customer.document_type,
                customer_document=work_order.customer.document_number,
                customer_address=work_order.customer.full_address,
                customer_city=work_order.customer.city or '',
                customer_department=work_order.customer.department or '',
                customer_phone=work_order.customer.phone or '',
                customer_email=work_order.customer.email or '',
                # Configuración fiscal
                tax_rate=work_order.workshop.default_tax_rate,
            )

            # Crear detalles de factura electrónica desde los ítems de la orden de trabajo
            subtotal = 0
            for item in work_order.details.all():
                # Usar la descripción del ítem o generar una apropiada
                description = item.description
                if not description:
                    if item.service:
                        description = f"Servicio: {item.service.name}"
                    elif item.part:
                        description = f"Repuesto: {item.part.name}"
                    else:
                        description = "Ítem de orden de trabajo"

                # Determinar código UNSPSC (simplificado)
                unspsc_code = ""
                if item.service:
                    unspsc_code = "81111500"  # Servicios de reparación de vehículos de motor
                elif item.part:
                    unspsc_code = "25170000"  # Partes de vehículos de motor

                electronic_invoice_detail = ElectronicInvoiceDetail.objects.create(
                    electronic_invoice=electronic_invoice,
                    description=description,
                    part_number=item.part.internal_code if item.part else "",
                    unspsc_code=unspsc_code,
                    brand_name=item.part.brand if item.part else "",
                    model_name=item.part.model if item.part else "",
                    quantity=item.part_quantity if item.part_quantity > 0 else item.service_quantity,
                    unit_code="NIU" if item.part else "E48",  # NIU para unidades, E48 para horas
                    unit_price=item.part_unit_price if item.part_unit_price > 0 else item.service_unit_price,
                    discount=0,  # Por ahora sin descuento
                )
                subtotal += electronic_invoice_detail.subtotal

                # Actualizar estadísticas del repuesto (ya se hizo en complete_item)
                if item.part and item.inventory_updated:
                    item.part.times_used += 1
                    item.part.last_sale_date = electronic_invoice.issue_date.date()
                    item.part.save()

            # Calcular totales
            tax_amount = subtotal * (electronic_invoice.tax_rate / 100) if electronic_invoice.tax_rate > 0 else 0
            total = subtotal + tax_amount

            # Actualizar factura electrónica
            electronic_invoice.subtotal = subtotal
            electronic_invoice.tax_amount = tax_amount
            electronic_invoice.total = total
            electronic_invoice.save()

            # Actualizar estadísticas del cliente
            work_order.customer.total_spent += total
            work_order.customer.total_visits += 1
            work_order.customer.last_visit = electronic_invoice.issue_date
            work_order.customer.save()

            # Cambiar estado de la OT a facturada
            work_order.change_status('invoiced', request.user, f'Factura electrónica DIAN {electronic_invoice.invoice_number} creada')

            serializer = ElectronicInvoiceSerializer(electronic_invoice)
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

            # Verificar que PDF esté disponible
            if not PDF_AVAILABLE or not generate_invoice_pdf:
                return Response({'error': 'Generador de PDF no disponible. Contacta al administrador.'},
                              status=status.HTTP_503_SERVICE_UNAVAILABLE)

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


# ===== VIEWSETS PARA FACTURACIÓN ELECTRÓNICA DIAN =====

class DianResolutionViewSet(viewsets.ModelViewSet):
    """API para gestión de resoluciones DIAN"""
    serializer_class = DianResolutionSerializer
    permission_classes = [IsAuthenticated]
    queryset = DianResolution.objects.all()

    def get_queryset(self):
        return DianResolution.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)


class ElectronicInvoiceViewSet(viewsets.ModelViewSet):
    """API para facturas electrónicas DIAN"""
    serializer_class = ElectronicInvoiceSerializer
    permission_classes = [IsAuthenticated]
    queryset = ElectronicInvoice.objects.all()

    def get_queryset(self):
        return ElectronicInvoice.objects.filter(workshop=self.request.user.workshop)

    def perform_create(self, serializer):
        serializer.save(workshop=self.request.user.workshop)

    @action(detail=True, methods=['post'])
    def generate_xml(self, request, pk=None):
        """Generar XML de la factura electrónica"""
        electronic_invoice = self.get_object()

        try:
            # Importar el generador XML (se implementará después)
            from .dian_xml_generator import generate_electronic_invoice_xml

            xml_content = generate_electronic_invoice_xml(electronic_invoice)
            electronic_invoice.xml_content = xml_content
            electronic_invoice.dian_status = 'generated'
            electronic_invoice.save()

            return Response({
                'message': 'XML generado exitosamente',
                'xml_length': len(xml_content)
            })

        except ImportError:
            return Response({
                'error': 'Generador XML no disponible'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({
                'error': f'Error generando XML: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def send_to_dian(self, request, pk=None):
        """Enviar factura a DIAN"""
        electronic_invoice = self.get_object()

        if electronic_invoice.dian_status != 'signed':
            return Response({
                'error': 'La factura debe estar firmada antes de enviarse a DIAN'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Simulación de envío a DIAN (se implementará la integración real después)
            electronic_invoice.dian_status = 'sent'
            electronic_invoice.dian_response_code = '00'  # Simulado
            electronic_invoice.dian_response_message = 'Factura enviada exitosamente'
            electronic_invoice.dian_response_date = timezone.now()
            electronic_invoice.save()

            return Response({
                'message': 'Factura enviada a DIAN exitosamente',
                'dian_response': {
                    'code': electronic_invoice.dian_response_code,
                    'message': electronic_invoice.dian_response_message
                }
            })

        except Exception as e:
            return Response({
                'error': f'Error enviando a DIAN: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def create_from_work_order(self, request):
        """Crear factura electrónica DIAN desde una orden de trabajo completada"""
        work_order_id = request.data.get('work_order_id')
        payment_method = request.data.get('payment_method', 'cash')

        try:
            work_order = WorkOrder.objects.get(
                id=work_order_id,
                workshop=request.user.workshop,
                status='completed'
            )

            # Verificar que no existe factura electrónica para esta OT
            if hasattr(work_order, 'electronic_invoice'):
                return Response({'error': 'Ya existe una factura electrónica para esta orden de trabajo'},
                              status=status.HTTP_400_BAD_REQUEST)

            # Verificar que el taller tenga resolución DIAN activa
            try:
                dian_resolution = DianResolution.objects.get(
                    workshop=work_order.workshop,
                    document_type='invoice',
                    is_active=True
                )
            except DianResolution.DoesNotExist:
                return Response({'error': 'No hay resolución DIAN activa para facturas electrónicas'},
                              status=status.HTTP_400_BAD_REQUEST)

            # Crear factura electrónica
            electronic_invoice = ElectronicInvoice.objects.create(
                workshop=work_order.workshop,
                customer=work_order.customer,
                work_order=work_order,
                dian_resolution=dian_resolution,
                payment_method=payment_method,
                # Información fiscal del taller
                workshop_nit=work_order.workshop.nit or '',
                workshop_name=work_order.workshop.legal_name or work_order.workshop.name,
                workshop_address=work_order.workshop.address,
                workshop_city=work_order.workshop.city or '',
                workshop_department=work_order.workshop.department or '',
                workshop_phone=work_order.workshop.phone or '',
                workshop_email=work_order.workshop.email or '',
                # Información del cliente
                customer_name=work_order.customer.full_name,
                customer_document_type=work_order.customer.document_type,
                customer_document=work_order.customer.document_number,
                customer_address=work_order.customer.full_address,
                customer_city=work_order.customer.city or '',
                customer_department=work_order.customer.department or '',
                customer_phone=work_order.customer.phone or '',
                customer_email=work_order.customer.email or '',
                # Configuración fiscal
                tax_rate=work_order.workshop.default_tax_rate,
            )

            # Crear detalles de factura electrónica desde los ítems de la orden de trabajo
            subtotal = 0
            for item in work_order.details.all():
                # Usar la descripción del ítem o generar una apropiada
                description = item.description
                if not description:
                    if item.service:
                        description = f"Servicio: {item.service.name}"
                    elif item.part:
                        description = f"Repuesto: {item.part.name}"
                    else:
                        description = "Ítem de orden de trabajo"

                # Determinar código UNSPSC (simplificado)
                unspsc_code = ""
                if item.service:
                    unspsc_code = "81111500"  # Servicios de reparación de vehículos de motor
                elif item.part:
                    unspsc_code = "25170000"  # Partes de vehículos de motor

                electronic_invoice_detail = ElectronicInvoiceDetail.objects.create(
                    electronic_invoice=electronic_invoice,
                    description=description,
                    part_number=item.part.internal_code if item.part else "",
                    unspsc_code=unspsc_code,
                    brand_name=item.part.brand if item.part else "",
                    model_name=item.part.model if item.part else "",
                    quantity=item.part_quantity if item.part_quantity > 0 else item.service_quantity,
                    unit_code="NIU" if item.part else "E48",  # NIU para unidades, E48 para horas
                    unit_price=item.part_unit_price if item.part_unit_price > 0 else item.service_unit_price,
                    discount=0,  # Por ahora sin descuento
                )
                subtotal += electronic_invoice_detail.subtotal

                # Actualizar estadísticas del repuesto (ya se hizo en complete_item)
                if item.part and item.inventory_updated:
                    item.part.times_used += 1
                    item.part.last_sale_date = electronic_invoice.issue_date.date()
                    item.part.save()

            # Calcular totales
            tax_amount = subtotal * (electronic_invoice.tax_rate / 100) if electronic_invoice.tax_rate > 0 else 0
            total = subtotal + tax_amount

            # Actualizar factura electrónica
            electronic_invoice.subtotal = subtotal
            electronic_invoice.tax_amount = tax_amount
            electronic_invoice.total = total
            electronic_invoice.save()

            # Actualizar estadísticas del cliente
            work_order.customer.total_spent += total
            work_order.customer.total_visits += 1
            work_order.customer.last_visit = electronic_invoice.issue_date
            work_order.customer.save()

            # Cambiar estado de la OT a facturada
            work_order.change_status('invoiced', request.user, f'Factura electrónica DIAN {electronic_invoice.invoice_number} creada')

            serializer = self.get_serializer(electronic_invoice)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except WorkOrder.DoesNotExist:
            return Response({'error': 'Orden de trabajo no encontrada o no completada'},
                          status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

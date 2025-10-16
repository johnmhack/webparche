from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Workshop, Customer, Vehicle, WorkOrder, Service, SparePart

User = get_user_model()


class WorkshopModelTest(TestCase):
    """Tests para el modelo Workshop"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_workshop_creation(self):
        """Test creación básica de taller"""
        workshop = Workshop.objects.create(
            owner=self.user,
            name='Test Workshop',
            nit='123456789'
        )
        self.assertEqual(workshop.name, 'Test Workshop')
        self.assertEqual(workshop.owner, self.user)
        self.assertTrue(workshop.is_subscription_active)

    def test_workshop_str(self):
        """Test representación string del taller"""
        workshop = Workshop.objects.create(
            owner=self.user,
            name='Test Workshop'
        )
        self.assertEqual(str(workshop), 'Test Workshop')


class CustomerModelTest(TestCase):
    """Tests para el modelo Customer"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='testpass123',
            first_name='Owner',
            last_name='User'
        )
        self.workshop = Workshop.objects.create(
            owner=self.user,
            name='Test Workshop'
        )

    def test_customer_creation(self):
        """Test creación básica de cliente"""
        customer = Customer.objects.create(
            workshop=self.workshop,
            first_name='John',
            last_name='Doe',
            document_type='cc',
            document_number='12345678'
        )
        self.assertEqual(customer.full_name, 'John Doe')
        self.assertEqual(customer.get_document_type_display(), 'Cédula de Ciudadanía')
        self.assertTrue(customer.is_active)

    def test_customer_unique_constraint(self):
        """Test restricción única de cliente por taller"""
        Customer.objects.create(
            workshop=self.workshop,
            first_name='John',
            last_name='Doe',
            document_type='cc',
            document_number='12345678'
        )

        # Intentar crear cliente duplicado debe fallar
        with self.assertRaises(Exception):
            Customer.objects.create(
                workshop=self.workshop,
                first_name='Jane',
                last_name='Smith',
                document_type='cc',
                document_number='12345678'
            )


class VehicleModelTest(TestCase):
    """Tests para el modelo Vehicle"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='testpass123'
        )
        self.workshop = Workshop.objects.create(owner=self.user, name='Test Workshop')
        self.customer = Customer.objects.create(
            workshop=self.workshop,
            first_name='John',
            last_name='Doe'
        )

    def test_vehicle_creation(self):
        """Test creación básica de vehículo"""
        vehicle = Vehicle.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            brand='Honda',
            model='Civic',
            year=2020,
            license_plate='ABC123'
        )
        self.assertEqual(vehicle.full_name, 'Honda Civic 2020')
        self.assertEqual(str(vehicle), 'Motocicleta: Honda Civic 2020 - ABC123')
        self.assertFalse(vehicle.needs_service)


class APITestCase(APITestCase):
    """Tests para la API REST"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.workshop = Workshop.objects.create(
            owner=self.user,
            name='Test Workshop'
        )
        self.client.force_authenticate(user=self.user)

    def test_dashboard_access(self):
        """Test acceso al dashboard"""
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('workshop', response.data)
        self.assertIn('stats', response.data)

    def test_customer_list(self):
        """Test listado de clientes"""
        url = reverse('customer-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)  # Es paginado

    def test_workshop_list(self):
        """Test listado de talleres (solo el propio)"""
        url = reverse('workshop-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Solo debe devolver el taller del usuario autenticado
        workshops = [w for w in response.data if w['owner'] == str(self.user.id)]
        self.assertEqual(len(workshops), 1)
        self.assertEqual(workshops[0]['name'], 'Test Workshop')


class ServiceModelTest(TestCase):
    """Tests para el modelo Service"""

    def setUp(self):
        self.user = User.objects.create_user(email='owner@example.com', password='testpass123')
        self.workshop = Workshop.objects.create(owner=self.user, name='Test Workshop')

    def test_service_creation(self):
        """Test creación básica de servicio"""
        service = Service.objects.create(
            workshop=self.workshop,
            name='Cambio de aceite',
            category='maintenance',
            estimated_hours=2,
            base_price=50000
        )
        self.assertEqual(service.estimated_cost, 50000)
        self.assertFalse(service.is_popular)
        self.assertEqual(str(service), 'Cambio de aceite - Mantenimiento')


class SparePartModelTest(TestCase):
    """Tests para el modelo SparePart"""

    def setUp(self):
        self.user = User.objects.create_user(email='owner@example.com', password='testpass123')
        self.workshop = Workshop.objects.create(owner=self.user, name='Test Workshop')

    def test_spare_part_creation(self):
        """Test creación básica de repuesto"""
        part = SparePart.objects.create(
            workshop=self.workshop,
            name='Filtro de aceite',
            category='filtros',
            stock_quantity=10,
            unit_cost=15000,
            sale_price=25000
        )
        self.assertAlmostEqual(part.profit_margin, 66.67, places=2)
        self.assertFalse(part.is_low_stock)
        self.assertEqual(part.stock_value, 150000)


class WorkOrderModelTest(TestCase):
    """Tests para el modelo WorkOrder"""

    def setUp(self):
        self.user = User.objects.create_user(email='owner@example.com', password='testpass123')
        self.workshop = Workshop.objects.create(owner=self.user, name='Test Workshop')
        self.customer = Customer.objects.create(
            workshop=self.workshop,
            first_name='John',
            last_name='Doe'
        )
        self.vehicle = Vehicle.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            brand='Honda',
            model='Civic',
            year=2020
        )

    def test_work_order_creation(self):
        """Test creación básica de orden de trabajo"""
        work_order = WorkOrder.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            vehicle=self.vehicle,
            title='Reparación de frenos',
            description='Cambio de pastillas de freno'
        )
        self.assertTrue(work_order.order_number.startswith('OT'))
        self.assertEqual(work_order.status, 'draft')
        self.assertFalse(work_order.is_overdue)
        self.assertEqual(work_order.total_cost, 0)

    def test_work_order_status_change(self):
        """Test cambio de estado de orden de trabajo"""
        work_order = WorkOrder.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            vehicle=self.vehicle,
            title='Test Order'
        )

        # Cambiar a aprobado
        work_order.change_status('approved', self.user)
        self.assertEqual(work_order.status, 'approved')
        self.assertIsNotNone(work_order.approved_date)

        # Verificar que se creó un log
        self.assertEqual(work_order.status_logs.count(), 1)

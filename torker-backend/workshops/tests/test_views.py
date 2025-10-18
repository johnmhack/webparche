"""
Tests de integración para las APIs (views)
"""
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from decimal import Decimal

from workshops.models import (
    User, Workshop, Customer, Vehicle, WorkOrder,
    DianResolution, ElectronicInvoice
)


class AuthenticationTest(APITestCase):
    """Tests para autenticación y registro"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')

    def test_user_registration(self):
        """Verificar registro de usuario"""
        data = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'workshopName': 'Mi Taller Nuevo'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        
        # Verificar que se creó el taller
        user = User.objects.get(email='newuser@example.com')
        self.assertTrue(hasattr(user, 'workshop'))
        self.assertEqual(user.workshop.name, 'Mi Taller Nuevo')

    def test_user_login(self):
        """Verificar login de usuario"""
        # Crear usuario primero
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        Workshop.objects.create(owner=user, name='Test Workshop')
        
        # Intentar login
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class WorkOrderAPITest(APITestCase):
    """Tests para API de órdenes de trabajo"""

    def setUp(self):
        # Crear usuario y taller
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='testpass123',
            first_name='Owner',
            last_name='Test'
        )
        self.workshop = Workshop.objects.create(
            owner=self.user,
            name='Taller Test'
        )
        
        # Crear cliente y vehículo
        self.customer = Customer.objects.create(
            workshop=self.workshop,
            first_name='Cliente',
            last_name='Test',
            document_type='cc',
            document_number='1234567890'
        )
        self.vehicle = Vehicle.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            vehicle_type='motorcycle',
            brand='Honda',
            model='CB190',
            year=2021
        )
        
        # Autenticar cliente
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_work_order(self):
        """Verificar creación de orden de trabajo"""
        url = reverse('workorder-list')
        data = {
            'customer': str(self.customer.id),
            'vehicle': str(self.vehicle.id),
            'title': 'Mantenimiento',
            'description': 'Cambio de aceite',
            'status': 'draft'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order_number', response.data)

    def test_list_work_orders(self):
        """Verificar listado de órdenes de trabajo"""
        # Crear algunas órdenes
        for i in range(5):
            WorkOrder.objects.create(
                workshop=self.workshop,
                customer=self.customer,
                vehicle=self.vehicle,
                title=f'OT {i}',
                status='draft'
            )
        
        url = reverse('workorder-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)

    def test_change_work_order_status(self):
        """Verificar cambio de estado de orden de trabajo"""
        work_order = WorkOrder.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            vehicle=self.vehicle,
            title='Test OT',
            status='draft'
        )
        
        url = reverse('workorder-change-status', kwargs={'pk': work_order.id})
        data = {
            'status': 'pending',
            'notes': 'Cambio a pendiente'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        work_order.refresh_from_db()
        self.assertEqual(work_order.status, 'pending')


class CustomerAPITest(APITestCase):
    """Tests para API de clientes"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='testpass123'
        )
        self.workshop = Workshop.objects.create(
            owner=self.user,
            name='Taller Test'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_customer(self):
        """Verificar creación de cliente"""
        url = reverse('customer-list')
        data = {
            'first_name': 'Nuevo',
            'last_name': 'Cliente',
            'document_type': 'cc',
            'document_number': '9999888877',
            'email': 'nuevo@example.com',
            'phone': '+573001234567'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'Nuevo')

    def test_list_customers(self):
        """Verificar listado de clientes"""
        # Crear clientes
        for i in range(3):
            Customer.objects.create(
                workshop=self.workshop,
                first_name=f'Cliente{i}',
                last_name='Test',
                document_type='cc',
                document_number=f'100000000{i}'
            )
        
        url = reverse('customer-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
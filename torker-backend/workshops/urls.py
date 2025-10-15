from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

router = DefaultRouter()
# Modelos principales
router.register(r'workshops', views.WorkshopViewSet)
router.register(r'customers', views.CustomerViewSet)
router.register(r'vehicles', views.VehicleViewSet)
router.register(r'mechanics', views.MechanicViewSet)
router.register(r'services', views.ServiceViewSet)
router.register(r'spare-parts', views.SparePartViewSet)

# Órdenes de trabajo y cotizaciones
router.register(r'work-orders', views.WorkOrderViewSet)
router.register(r'quotations', views.QuotationViewSet)

# Facturación DIAN
router.register(r'invoices', views.InvoiceViewSet)
router.register(r'electronic-invoices', views.ElectronicInvoiceViewSet, basename='electronic-invoice')
router.register(r'dian-resolutions', views.DianResolutionViewSet, basename='dian-resolution')
router.register(r'credit-notes', views.CreditNoteViewSet)
router.register(r'debit-notes', views.DebitNoteViewSet)

# Otros
router.register(r'appointments', views.AppointmentViewSet)

# Mantener compatibilidad
router.register(r'motorcycles', views.VehicleViewSet, basename='motorcycle')  # Alias con basename único
router.register(r'employees', views.MechanicViewSet, basename='employee')     # Alias con basename único
router.register(r'parts', views.SparePartViewSet, basename='part')            # Alias con basename único

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/register/', views.RegisterView.as_view(), name='register'),
    path('api/dashboard/', views.DashboardView.as_view(), name='dashboard'),
    # TEMPORAL: Endpoint para crear usuario de prueba
    path('api/create-test-user/', views.create_test_user, name='create_test_user'),
]
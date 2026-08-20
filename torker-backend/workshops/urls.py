from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views
from .supabase.views import (
    SupabaseCerrarOrdenView,
    SupabaseCitaCancelarView,
    SupabaseCitasView,
    SupabaseClienteDetailView,
    SupabaseClientesView,
    SupabaseHealthView,
    SupabaseMotoBuscarView,
    SupabaseOrdenesView,
    SupabaseRepuestoDetailView,
    SupabaseRepuestosView,
    SupabaseTallerView,
    SupabaseTiposServicioSembrarView,
    SupabaseTiposServicioView,
)

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
router.register(r'electronic-invoices', views.ElectronicInvoiceViewSet)
router.register(r'invoices', views.InvoiceViewSet)
router.register(r'credit-notes', views.CreditNoteViewSet)
router.register(r'debit-notes', views.DebitNoteViewSet)

# Agenda y citas
router.register(r'service-types', views.ServiceTypeViewSet)
router.register(r'appointments', views.AppointmentViewSet)

# Mantener compatibilidad
router.register(r'motorcycles', views.VehicleViewSet, basename='motorcycle')  # Alias con basename único
router.register(r'employees', views.MechanicViewSet, basename='employee')     # Alias con basename único
router.register(r'parts', views.SparePartViewSet, basename='part')            # Alias con basename único

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    # Integración Supabase (ecosistema Parche) — DIAN postergado
    path('supabase/health/', SupabaseHealthView.as_view(), name='supabase_health'),
    path('supabase/taller/', SupabaseTallerView.as_view(), name='supabase_taller'),
    path('supabase/motos/buscar/', SupabaseMotoBuscarView.as_view(), name='supabase_moto_buscar'),
    path('supabase/ordenes/', SupabaseOrdenesView.as_view(), name='supabase_ordenes'),
    path('supabase/ordenes/<uuid:orden_id>/cerrar/', SupabaseCerrarOrdenView.as_view(), name='supabase_cerrar_orden'),
    path('supabase/clientes/', SupabaseClientesView.as_view(), name='supabase_clientes'),
    path('supabase/clientes/<uuid:cliente_id>/', SupabaseClienteDetailView.as_view(), name='supabase_cliente_detail'),
    path('supabase/tipos-servicio/', SupabaseTiposServicioView.as_view(), name='supabase_tipos_servicio'),
    path('supabase/tipos-servicio/sembrar/', SupabaseTiposServicioSembrarView.as_view(), name='supabase_tipos_servicio_sembrar'),
    path('supabase/citas/', SupabaseCitasView.as_view(), name='supabase_citas'),
    path('supabase/citas/<uuid:cita_id>/cancelar/', SupabaseCitaCancelarView.as_view(), name='supabase_cita_cancelar'),
    path('supabase/repuestos/', SupabaseRepuestosView.as_view(), name='supabase_repuestos'),
    path('supabase/repuestos/<uuid:repuesto_id>/', SupabaseRepuestoDetailView.as_view(), name='supabase_repuesto_detail'),
    # TEMPORAL: Endpoint para crear usuario de prueba
    path('create-test-user/', views.create_test_user, name='create_test_user'),
]
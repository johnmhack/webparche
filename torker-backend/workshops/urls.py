from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

router = DefaultRouter()
router.register(r'workshops', views.WorkshopViewSet)
router.register(r'customers', views.CustomerViewSet)
router.register(r'motorcycles', views.MotorcycleViewSet)
router.register(r'employees', views.EmployeeViewSet)
router.register(r'parts', views.PartViewSet)
router.register(r'work-orders', views.WorkOrderViewSet)
router.register(r'appointments', views.AppointmentViewSet)
router.register(r'invoices', views.InvoiceViewSet)
router.register(r'credit-notes', views.CreditNoteViewSet)
router.register(r'debit-notes', views.DebitNoteViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/register/', views.RegisterView.as_view(), name='register'),
    path('api/dashboard/', views.DashboardView.as_view(), name='dashboard'),
    # TEMPORAL: Endpoint para crear usuario de prueba
    path('api/create-test-user/', views.create_test_user, name='create_test_user'),
]
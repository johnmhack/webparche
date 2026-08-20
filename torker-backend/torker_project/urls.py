"""
URL configuration for torker_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from .spa_views import serve_dashboard_spa, serve_landing

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('workshops.urls')),
    path('', serve_landing, name='landing'),
    # SPA React — con y sin barra final (evita caer en static /pages/)
    path('pages/dashboard/app', serve_dashboard_spa, name='dashboard_spa_root'),
    path('pages/dashboard/app/', serve_dashboard_spa, name='dashboard_spa'),
    path('pages/dashboard/app/<path:resource_path>', serve_dashboard_spa, name='dashboard_spa_path'),
    path('pages/dashboard/', RedirectView.as_view(url='/pages/dashboard/app/login', permanent=False)),
    path('pages/torker/', RedirectView.as_view(url='/pages/dashboard/app/login', permanent=False)),
    path('pages/coming-soon.html', RedirectView.as_view(url='/pages/dashboard/app/login', permanent=True)),
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Servir archivos desde assets y pages
    urlpatterns += static('/assets/', document_root=os.path.join(settings.BASE_DIR, '..', 'assets'))
    urlpatterns += static('/pages/', document_root=os.path.join(settings.BASE_DIR, '..', 'pages'))

"""Sirve el dashboard React (SPA) desde pages/dashboard/app/."""
from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.views.static import serve

DASHBOARD_APP_DIR = Path(settings.BASE_DIR).parent / 'pages' / 'dashboard' / 'app'


def serve_dashboard_spa(request, resource_path: str = ''):
    """
    Archivos estáticos del build (JS/CSS) se sirven directo.
    Cualquier otra ruta devuelve index.html para React Router.
    """
    resource_path = (resource_path or '').lstrip('/')

    if resource_path:
        target = DASHBOARD_APP_DIR / resource_path
        if target.is_file():
            return serve(request, resource_path, document_root=str(DASHBOARD_APP_DIR))

    index = DASHBOARD_APP_DIR / 'index.html'
    if index.is_file():
        return FileResponse(index.open('rb'), content_type='text/html; charset=utf-8')

    raise Http404('Dashboard React no encontrado. Ejecuta: cd torker-dashboard && npm run build')

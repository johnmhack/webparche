from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import propietario_id_desde_request
from .client import supabase_configurado
from .services import (
    SupabaseError,
    actualizar_taller,
    buscar_moto_por_placa,
    cerrar_orden_y_registrar_historial,
    crear_orden_trabajo,
    crear_taller,
    listar_ordenes_taller,
    obtener_taller_por_propietario,
)
from .services_clientes import (
    actualizar_cliente,
    cancelar_cita,
    crear_cita,
    crear_cliente,
    listar_citas,
    listar_clientes,
    listar_tipos_servicio,
    sembrar_tipos_servicio_default,
)


def _propietario_id(request) -> str | None:
    return propietario_id_desde_request(request)


def _respuesta_error(exc: SupabaseError):
    return Response({'error': str(exc), 'detalle': exc.detalle}, status=status.HTTP_400_BAD_REQUEST)


class SupabaseAPIView(APIView):
    """Sin JWT de Django — usa token Supabase o X-Propietario-Id."""
    authentication_classes = []
    permission_classes = [AllowAny]


class SupabaseHealthView(SupabaseAPIView):

    def get(self, request):
        return Response({
            'supabase_configurado': supabase_configurado(),
            'dian': 'postergado',
        })


class SupabaseTallerView(SupabaseAPIView):
    """CRUD de talleres en Supabase (ecosistema Parche)."""

    def get(self, request):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        if not propietario_id:
            return Response({'error': 'Header X-Propietario-Id requerido'}, status=400)

        try:
            taller = obtener_taller_por_propietario(propietario_id)
            if not taller:
                return Response({'error': 'Taller no encontrado'}, status=404)
            return Response(taller)
        except SupabaseError as exc:
            return _respuesta_error(exc)

    def post(self, request):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        if not propietario_id:
            return Response({'error': 'Header X-Propietario-Id requerido'}, status=400)

        if not request.data.get('nombre'):
            return Response({'error': 'nombre es obligatorio'}, status=400)

        try:
            existente = obtener_taller_por_propietario(propietario_id)
            if existente:
                return Response({'error': 'Este usuario ya tiene un taller', 'taller': existente}, status=409)
            taller = crear_taller(propietario_id, request.data)
            return Response(taller, status=201)
        except SupabaseError as exc:
            return _respuesta_error(exc)

    def patch(self, request):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        taller_id = request.data.get('taller_id')
        if not propietario_id or not taller_id:
            return Response({'error': 'X-Propietario-Id y taller_id requeridos'}, status=400)

        try:
            taller = actualizar_taller(taller_id, propietario_id, request.data)
            return Response(taller)
        except SupabaseError as exc:
            return _respuesta_error(exc)


class SupabaseMotoBuscarView(SupabaseAPIView):

    def get(self, request):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        placa = request.query_params.get('placa')
        if not placa:
            return Response({'error': 'placa requerida'}, status=400)

        try:
            moto = buscar_moto_por_placa(placa)
            if not moto:
                return Response({'error': 'Moto no encontrada'}, status=404)
            return Response(moto)
        except SupabaseError as exc:
            return _respuesta_error(exc)


class SupabaseOrdenesView(SupabaseAPIView):

    def get(self, request):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        taller_id = request.query_params.get('taller_id')
        if not propietario_id or not taller_id:
            return Response({'error': 'X-Propietario-Id y taller_id requeridos'}, status=400)

        try:
            ordenes = listar_ordenes_taller(taller_id, propietario_id)
            return Response(ordenes)
        except SupabaseError as exc:
            return _respuesta_error(exc)

    def post(self, request):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        taller_id = request.data.get('taller_id')
        if not propietario_id or not taller_id:
            return Response({'error': 'X-Propietario-Id y taller_id requeridos'}, status=400)

        try:
            orden = crear_orden_trabajo(taller_id, propietario_id, request.data)
            return Response(orden, status=201)
        except SupabaseError as exc:
            return _respuesta_error(exc)


class SupabaseCerrarOrdenView(SupabaseAPIView):

    def post(self, request, orden_id):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        if not propietario_id:
            return Response({'error': 'Header X-Propietario-Id requerido'}, status=400)

        try:
            resultado = cerrar_orden_y_registrar_historial(orden_id, propietario_id, request.data)
            return Response(resultado)
        except SupabaseError as exc:
            return _respuesta_error(exc)


class SupabaseClientesView(SupabaseAPIView):

    def get(self, request):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        taller_id = request.query_params.get('taller_id')
        if not propietario_id or not taller_id:
            return Response({'error': 'X-Propietario-Id y taller_id requeridos'}, status=400)

        try:
            return Response(listar_clientes(taller_id, propietario_id))
        except SupabaseError as exc:
            return _respuesta_error(exc)

    def post(self, request):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        taller_id = request.query_params.get('taller_id') or request.data.get('taller_id')
        if not propietario_id or not taller_id:
            return Response({'error': 'X-Propietario-Id y taller_id requeridos'}, status=400)

        try:
            cliente = crear_cliente(taller_id, propietario_id, request.data)
            return Response(cliente, status=201)
        except SupabaseError as exc:
            return _respuesta_error(exc)


class SupabaseClienteDetailView(SupabaseAPIView):

    def patch(self, request, cliente_id):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        taller_id = request.data.get('taller_id')
        if not propietario_id or not taller_id:
            return Response({'error': 'X-Propietario-Id y taller_id requeridos'}, status=400)

        try:
            cliente = actualizar_cliente(cliente_id, taller_id, propietario_id, request.data)
            return Response(cliente)
        except SupabaseError as exc:
            return _respuesta_error(exc)


class SupabaseTiposServicioView(SupabaseAPIView):

    def get(self, request):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        taller_id = request.query_params.get('taller_id')
        if not propietario_id or not taller_id:
            return Response({'error': 'X-Propietario-Id y taller_id requeridos'}, status=400)

        try:
            return Response(listar_tipos_servicio(taller_id, propietario_id))
        except SupabaseError as exc:
            return _respuesta_error(exc)


class SupabaseTiposServicioSembrarView(SupabaseAPIView):

    def post(self, request):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        taller_id = request.data.get('taller_id')
        if not propietario_id or not taller_id:
            return Response({'error': 'X-Propietario-Id y taller_id requeridos'}, status=400)

        try:
            sembrar_tipos_servicio_default(taller_id, propietario_id)
            return Response(listar_tipos_servicio(taller_id, propietario_id))
        except SupabaseError as exc:
            return _respuesta_error(exc)


class SupabaseCitasView(SupabaseAPIView):

    def get(self, request):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        taller_id = request.query_params.get('taller_id')
        if not propietario_id or not taller_id:
            return Response({'error': 'X-Propietario-Id y taller_id requeridos'}, status=400)

        try:
            return Response(listar_citas(taller_id, propietario_id))
        except SupabaseError as exc:
            return _respuesta_error(exc)

    def post(self, request):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        taller_id = request.data.get('taller_id')
        if not propietario_id or not taller_id:
            return Response({'error': 'X-Propietario-Id y taller_id requeridos'}, status=400)

        try:
            cita = crear_cita(taller_id, propietario_id, request.data)
            return Response(cita, status=201)
        except SupabaseError as exc:
            return _respuesta_error(exc)


class SupabaseCitaCancelarView(SupabaseAPIView):

    def post(self, request, cita_id):
        if not supabase_configurado():
            return Response({'error': 'Supabase no configurado'}, status=503)

        propietario_id = _propietario_id(request)
        taller_id = request.data.get('taller_id')
        if not propietario_id or not taller_id:
            return Response({'error': 'X-Propietario-Id y taller_id requeridos'}, status=400)

        try:
            cita = cancelar_cita(cita_id, taller_id, propietario_id, request.data.get('notes'))
            return Response(cita)
        except SupabaseError as exc:
            return _respuesta_error(exc)

"""
Cliente API para integración con DIAN
Incluye simulación para desarrollo y cliente real para producción
"""

import requests
import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DianEnvironment(Enum):
    """Ambientes DIAN disponibles"""
    SIMULATION = "simulation"
    TESTING = "testing"
    PRODUCTION = "production"


class DianApiResponse:
    """Respuesta estandarizada de la API DIAN"""

    def __init__(self, success: bool, cufe: str = None, message: str = None,
                 errors: List[str] = None, status_code: int = None):
        self.success = success
        self.cufe = cufe
        self.message = message
        self.errors = errors or []
        self.status_code = status_code
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'cufe': self.cufe,
            'message': self.message,
            'errors': self.errors,
            'status_code': self.status_code,
            'timestamp': self.timestamp.isoformat()
        }


class DianApiClient:
    """Cliente para APIs de la DIAN"""

    # URLs base por ambiente
    BASE_URLS = {
        DianEnvironment.TESTING: "https://vpfe-hab.dian.gov.co",
        DianEnvironment.PRODUCTION: "https://vpfe.dian.gov.co",
        DianEnvironment.SIMULATION: "http://localhost:8000/api/dian/simulation"  # Simulación local
    }

    def __init__(self, environment: DianEnvironment = DianEnvironment.SIMULATION,
                 nit: str = None, software_id: str = None, software_pin: str = None):
        self.environment = environment
        self.base_url = self.BASE_URLS[environment]
        self.nit = nit
        self.software_id = software_id
        self.software_pin = software_pin

        # Configurar logging
        self.logger = logging.getLogger(f"DianApiClient-{environment.value}")

    def send_invoice(self, xml_content: str, test_set_id: str = None) -> DianApiResponse:
        """
        Envía factura electrónica a la DIAN

        Args:
            xml_content: Contenido XML de la factura firmada
            test_set_id: ID del set de pruebas (solo para ambiente de pruebas)

        Returns:
            DianApiResponse con resultado del envío
        """
        if self.environment == DianEnvironment.SIMULATION:
            return self._simulate_send_invoice(xml_content)

        try:
            # Endpoint real de DIAN
            endpoint = f"{self.base_url}/VpfeReceptorWs/VpfeReceptorSvc.svc"

            # Headers para SOAP
            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/IVpfeReceptorSvc/EnviarFacturaElectronica'
            }

            # Crear envelope SOAP
            soap_envelope = self._create_soap_envelope(xml_content, test_set_id)

            self.logger.info(f"Enviando factura a DIAN - Ambiente: {self.environment.value}")

            response = requests.post(endpoint, data=soap_envelope, headers=headers, timeout=30)

            return self._parse_dian_response(response)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error de conexión con DIAN: {str(e)}")
            return DianApiResponse(
                success=False,
                message="Error de conexión con DIAN",
                errors=[str(e)],
                status_code=500
            )

    def _create_soap_envelope(self, xml_content: str, test_set_id: str = None) -> str:
        """Crea envelope SOAP para envío a DIAN"""
        # Calcular hash del XML para integridad
        xml_hash = hashlib.sha256(xml_content.encode('utf-8')).hexdigest()

        envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:tem="http://tempuri.org/">
    <soap:Header/>
    <soap:Body>
        <tem:EnviarFacturaElectronica>
            <tem:nitEmisor>{self.nit}</tem:nitEmisor>
            <tem:idSoftware>{self.software_id}</tem:idSoftware>
            <tem:pin>{self.software_pin}</tem:pin>
            <tem:facturaXml><![CDATA[{xml_content}]]></tem:facturaXml>
            <tem:emailNotificacion>facturas@torker.com</tem:emailNotificacion>"""

        if test_set_id:
            envelope += f"""
            <tem:idSetPruebas>{test_set_id}</tem:idSetPruebas>"""

        envelope += """
        </tem:EnviarFacturaElectronica>
    </soap:Body>
</soap:Envelope>"""

        return envelope

    def _parse_dian_response(self, response: requests.Response) -> DianApiResponse:
        """Parsea respuesta SOAP de DIAN"""
        try:
            if response.status_code == 200:
                # Parsear respuesta SOAP exitosa
                # Aquí iría el parsing real del XML de respuesta
                return DianApiResponse(
                    success=True,
                    cufe=self._extract_cufe_from_response(response.text),
                    message="Factura enviada exitosamente",
                    status_code=200
                )
            else:
                return DianApiResponse(
                    success=False,
                    message="Error en respuesta DIAN",
                    errors=[f"Status code: {response.status_code}"],
                    status_code=response.status_code
                )

        except Exception as e:
            return DianApiResponse(
                success=False,
                message="Error procesando respuesta DIAN",
                errors=[str(e)],
                status_code=500
            )

    def _extract_cufe_from_response(self, response_xml: str) -> str:
        """Extrae CUFE de respuesta DIAN (simplificado)"""
        # En implementación real, parsear XML de respuesta
        # Por ahora, generar CUFE simulado
        return str(uuid.uuid4()).replace('-', '').upper()

    def _simulate_send_invoice(self, xml_content: str) -> DianApiResponse:
        """Simula envío de factura para desarrollo"""
        self.logger.info("SIMULACIÓN: Enviando factura a DIAN")

        # Simular diferentes escenarios
        import random
        scenario = random.choice(['success', 'validation_error', 'connection_error'])

        if scenario == 'success':
            # Simular éxito
            simulated_cufe = str(uuid.uuid4()).replace('-', '').upper()
            return DianApiResponse(
                success=True,
                cufe=simulated_cufe,
                message="Factura enviada exitosamente (SIMULADO)",
                status_code=200
            )

        elif scenario == 'validation_error':
            # Simular error de validación
            return DianApiResponse(
                success=False,
                message="Error de validación DIAN (SIMULADO)",
                errors=[
                    "El NIT del emisor no está registrado en el ambiente de pruebas",
                    "La resolución de facturación no es válida"
                ],
                status_code=400
            )

        else:
            # Simular error de conexión
            return DianApiResponse(
                success=False,
                message="Error de conexión con DIAN (SIMULADO)",
                errors=["Timeout en conexión"],
                status_code=500
            )

    def get_invoice_status(self, cufe: str) -> DianApiResponse:
        """Consulta estado de factura en DIAN"""
        if self.environment == DianEnvironment.SIMULATION:
            return self._simulate_get_status(cufe)

        try:
            endpoint = f"{self.base_url}/consultas/documentos/{cufe}"

            response = requests.get(endpoint, timeout=30)

            if response.status_code == 200:
                return DianApiResponse(
                    success=True,
                    message="Factura procesada correctamente",
                    status_code=200
                )
            else:
                return DianApiResponse(
                    success=False,
                    message="Factura no encontrada o con errores",
                    status_code=response.status_code
                )

        except requests.exceptions.RequestException as e:
            return DianApiResponse(
                success=False,
                message="Error consultando estado",
                errors=[str(e)],
                status_code=500
            )

    def _simulate_get_status(self, cufe: str) -> DianApiResponse:
        """Simula consulta de estado"""
        self.logger.info(f"SIMULACIÓN: Consultando estado de CUFE {cufe}")

        # Simular estados posibles
        import random
        status = random.choice(['processed', 'processing', 'rejected'])

        if status == 'processed':
            return DianApiResponse(
                success=True,
                message="Factura procesada correctamente (SIMULADO)",
                status_code=200
            )
        elif status == 'processing':
            return DianApiResponse(
                success=True,
                message="Factura en proceso de validación (SIMULADO)",
                status_code=202
            )
        else:
            return DianApiResponse(
                success=False,
                message="Factura rechazada por validación (SIMULADO)",
                errors=["Error de formato en XML"],
                status_code=400
            )

    def download_invoice(self, cufe: str, format_type: str = 'xml') -> Tuple[bool, str]:
        """
        Descarga factura procesada desde DIAN

        Args:
            cufe: Código único de factura
            format_type: 'xml', 'pdf', 'json'

        Returns:
            Tuple de (éxito, contenido)
        """
        if self.environment == DianEnvironment.SIMULATION:
            return self._simulate_download(cufe, format_type)

        try:
            endpoint = f"{self.base_url}/descargas/documentos/{cufe}"
            params = {'formato': format_type}

            response = requests.get(endpoint, params=params, timeout=30)

            if response.status_code == 200:
                return True, response.text
            else:
                return False, f"Error descargando documento: {response.status_code}"

        except requests.exceptions.RequestException as e:
            return False, f"Error de conexión: {str(e)}"

    def _simulate_download(self, cufe: str, format_type: str) -> Tuple[bool, str]:
        """Simula descarga de documento"""
        self.logger.info(f"SIMULACIÓN: Descargando {format_type} para CUFE {cufe}")

        if format_type == 'xml':
            return True, f"<Invoice><!-- XML simulado para CUFE {cufe} --></Invoice>"
        elif format_type == 'pdf':
            return True, f"PDF simulado para CUFE {cufe}"
        else:
            return True, f'{{"cufe": "{cufe}", "status": "simulated"}}'


class DianApiService:
    """Servicio de alto nivel para operaciones DIAN"""

    def __init__(self, environment: DianEnvironment = DianEnvironment.SIMULATION):
        self.environment = environment
        self.client = DianApiClient(environment=environment)

    def submit_invoice(self, invoice, xml_content: str) -> Dict:
        """
        Procesa envío completo de factura a DIAN

        Args:
            invoice: Instancia de ElectronicInvoice
            xml_content: XML de la factura

        Returns:
            Dict con resultado del procesamiento
        """
        result = {
            'success': False,
            'cufe': None,
            'message': '',
            'errors': [],
            'status': 'draft'
        }

        try:
            # 1. Enviar factura
            send_response = self.client.send_invoice(xml_content)

            if send_response.success:
                # 2. Actualizar factura con CUFE
                invoice.cufe = send_response.cufe
                invoice.dian_status = 'sent'
                invoice.save()

                # 3. Esperar un momento y consultar estado
                import time
                time.sleep(2)  # Simular procesamiento

                status_response = self.client.get_invoice_status(send_response.cufe)

                if status_response.success:
                    invoice.dian_status = 'processed'
                    result['status'] = 'processed'
                else:
                    invoice.dian_status = 'rejected'
                    result['status'] = 'rejected'
                    result['errors'].extend(status_response.errors)

                invoice.save()

                result.update({
                    'success': True,
                    'cufe': send_response.cufe,
                    'message': 'Factura procesada exitosamente'
                })

            else:
                # Error en envío
                invoice.dian_status = 'send_failed'
                invoice.save()

                result.update({
                    'message': send_response.message,
                    'errors': send_response.errors
                })

        except Exception as e:
            result.update({
                'message': 'Error interno procesando factura',
                'errors': [str(e)]
            })

        return result
from django.core.management.base import BaseCommand
from django.utils import timezone
from workshops.models import Workshop, Customer, Part, ElectronicInvoice, ElectronicInvoiceDetail
from workshops.dian_xml_generator import DianXmlGenerator, DianXmlValidator
from workshops.dian_schematron_validator import DianSchematronValidator
from workshops.dian_api_client import DianApiClient, DianEnvironment, DianApiService


class Command(BaseCommand):
    help = 'Crear y probar generación de XML DIAN con datos de prueba'

    def add_arguments(self, parser):
        """Agregar argumentos opcionales al comando"""
        parser.add_argument(
            '--environment',
            type=str,
            choices=['simulation', 'testing', 'production'],
            default='simulation',
            help='Ambiente DIAN a utilizar'
        )

        parser.add_argument(
            '--save-xml',
            action='store_true',
            help='Guardar XML generado en archivo'
        )

    def handle(self, *args, **options):
        """Método principal con argumentos"""
        # Usar el ambiente especificado
        env_map = {
            'simulation': DianEnvironment.SIMULATION,
            'testing': DianEnvironment.TESTING,
            'production': DianEnvironment.PRODUCTION
        }

        environment = env_map.get(options.get('environment', 'simulation'), DianEnvironment.SIMULATION)

        try:
            # Obtener taller de prueba
            workshop = Workshop.objects.first()
            if not workshop:
                self.stdout.write(self.style.ERROR('No hay talleres registrados'))
                return

            # Obtener o crear cliente de prueba
            customer, created = Customer.objects.get_or_create(
                workshop=workshop,
                document_number='123456789',
                defaults={
                    'first_name': 'Juan',
                    'last_name': 'Pérez',
                    'document_type': 'cc',
                    'email': 'juan@example.com',
                    'phone': '3001234567',
                    'address': 'Calle 123 #45-67',
                    'city': 'Bogotá',
                    'department': 'Cundinamarca'
                }
            )

            # Obtener o crear producto de prueba
            part, created = Part.objects.get_or_create(
                workshop=workshop,
                name='Filtro de aceite',
                defaults={
                    'description': 'Filtro de aceite para motocicleta',
                    'part_number': 'FLT-001',
                    'category': 'filtros',
                    'stock_quantity': 50,
                    'unit_cost': 15000,
                    'sale_price': 25000,
                    'is_taxable': True
                }
            )

            # Crear factura electrónica de prueba
            invoice = ElectronicInvoice.objects.create(
                workshop=workshop,
                customer=customer,
                dian_resolution=workshop.dian_resolutions.first(),
                issue_date=timezone.now(),
                issue_time=timezone.now().time(),
                due_date=timezone.now().date() + timezone.timedelta(days=30),

                # Información del taller
                workshop_nit=workshop.nit or '2022516216',
                workshop_name=workshop.name,
                workshop_address=workshop.address or 'Dirección del taller',
                workshop_city=workshop.city or 'Bogotá',
                workshop_department=workshop.department or 'Cundinamarca',
                workshop_phone=workshop.phone,
                workshop_email=workshop.email,

                # Información del cliente
                customer_name=customer.full_name,
                customer_document_type=customer.document_type,
                customer_document=customer.document_number,
                customer_address=customer.full_address,
                customer_city=customer.city,
                customer_department=customer.department,
                customer_phone=customer.phone,
                customer_email=customer.email,

                # Totales
                subtotal=25000,
                discount=0,
                tax_rate=19,
                tax_amount=4750,
                total=29750,

                # Estado
                dian_status='draft',
                payment_status='pending',
                payment_method='cash',
                notes='Factura de prueba para validación XML DIAN'
            )

            # Crear detalle de factura
            detail = ElectronicInvoiceDetail.objects.create(
                electronic_invoice=invoice,
                part=part,
                description=f'{part.name} - {part.description}',
                part_number=part.part_number,
                quantity=1,
                unit_price=25000,
                discount=0,
                tax_rate=19
            )

            self.stdout.write(self.style.SUCCESS(f'Factura electrónica creada: {invoice.invoice_number}'))

            # Generar XML (sin pretty print para evitar problemas de namespaces)
            xml_generator = DianXmlGenerator(invoice)
            xml_content = xml_generator.get_xml_string(pretty_print=False)

            # Guardar XML en la factura
            invoice.xml_content = xml_content
            invoice.save()

            self.stdout.write(self.style.SUCCESS('XML generado exitosamente'))

            # Mostrar primeras líneas del XML para debug
            lines = xml_content.split('\n')
            self.stdout.write('Primeras líneas del XML generado:')
            for i, line in enumerate(lines[:5]):
                self.stdout.write(f'  {i+1}: {line[:100]}...')

            # Validar XML
            validator = DianXmlValidator(xml_content)
            is_valid = validator.validate_basic_structure()

            if is_valid:
                self.stdout.write(self.style.SUCCESS('Validacion XML basica: PASO'))
            else:
                self.stdout.write(self.style.ERROR('Validacion XML basica: FALLO'))
                for error in validator.get_validation_errors():
                    self.stdout.write(self.style.ERROR(f'   - {error}'))

            # Validar XML con validador básico
            basic_validator = DianXmlValidator(xml_content)
            basic_valid = basic_validator.validate_basic_structure()

            # Validar XML con Schematron
            schematron_validator = DianSchematronValidator(xml_content)
            schematron_valid = schematron_validator.validate_invoice()

            # Resultados de validación
            self.stdout.write('\n=== RESULTADOS DE VALIDACION ===')

            if basic_valid:
                self.stdout.write(self.style.SUCCESS('✅ Validacion XML basica: PASO'))
            else:
                self.stdout.write(self.style.ERROR('❌ Validacion XML basica: FALLO'))
                for error in basic_validator.get_validation_errors():
                    self.stdout.write(self.style.ERROR(f'   - {error}'))

            if schematron_valid:
                self.stdout.write(self.style.SUCCESS('✅ Validacion Schematron DIAN: PASO'))
            else:
                self.stdout.write(self.style.ERROR('❌ Validacion Schematron DIAN: FALLO'))
                for error in schematron_validator.get_validation_errors():
                    self.stdout.write(self.style.ERROR(f'   - {error}'))

            # Mostrar warnings si existen
            warnings = schematron_validator.get_validation_warnings()
            if warnings:
                self.stdout.write(self.style.WARNING('⚠️  Advertencias:'))
                for warning in warnings:
                    self.stdout.write(self.style.WARNING(f'   - {warning}'))

            # Validación general
            overall_valid = basic_valid and schematron_valid
            if overall_valid:
                self.stdout.write(self.style.SUCCESS('🎉 VALIDACION COMPLETA: TODAS LAS PRUEBAS PASARON'))

                # Si validación pasa, intentar envío simulado a DIAN
                self.stdout.write('\n🚀 PRUEBA DE ENVÍO A DIAN (SIMULADO):')
                self._test_dian_submission(xml_content, invoice)

            else:
                self.stdout.write(self.style.ERROR('❌ VALIDACION COMPLETA: ERRORES DETECTADOS'))

            # Mostrar información de la factura
            self.stdout.write('\n' + '='*50)
            self.stdout.write('INFORMACIÓN DE LA FACTURA DE PRUEBA')
            self.stdout.write('='*50)
            self.stdout.write(f'Número: {invoice.invoice_number}')
            self.stdout.write(f'CUDE: {invoice.cude}')
            self.stdout.write(f'Fecha: {invoice.issue_date.strftime("%Y-%m-%d %H:%M:%S")}')
            self.stdout.write(f'Cliente: {invoice.customer_name}')
            self.stdout.write(f'Subtotal: ${invoice.subtotal:,.0f}')
            self.stdout.write(f'IVA (19%): ${invoice.tax_amount:,.0f}')
            self.stdout.write(f'Total: ${invoice.total:,.0f}')
            self.stdout.write(f'Estado DIAN: {invoice.get_dian_status_display()}')
            self.stdout.write('='*50)

            # Guardar XML en archivo para revisión (solo si validación básica pasa)
            if basic_valid:
                filename = f'factura_prueba_{invoice.invoice_number}.xml'
                xml_generator.save_xml_file(filename)
                self.stdout.write(self.style.SUCCESS(f'XML guardado en: {filename}'))
            else:
                self.stdout.write(self.style.WARNING('XML no guardado debido a errores de validacion'))

    def _test_dian_submission(self, xml_content: str, invoice):
        """Prueba envío simulado a DIAN"""
        try:
            # Crear cliente API en modo simulación
            api_client = DianApiClient(environment=DianEnvironment.SIMULATION)

            # Enviar factura
            self.stdout.write('📤 Enviando factura a DIAN (simulado)...')
            response = api_client.send_invoice(xml_content)

            if response.success:
                self.stdout.write(self.style.SUCCESS(f'✅ Factura enviada exitosamente'))
                self.stdout.write(self.style.SUCCESS(f'   CUFE: {response.cufe}'))

                # Actualizar factura con CUFE simulado
                invoice.cufe = response.cufe
                invoice.dian_status = 'sent'
                invoice.save()

                # Consultar estado
                self.stdout.write('🔍 Consultando estado en DIAN...')
                status_response = api_client.get_invoice_status(response.cufe)

                if status_response.success:
                    self.stdout.write(self.style.SUCCESS('✅ Factura procesada correctamente'))
                    invoice.dian_status = 'processed'
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Factura en proceso de validación'))
                    invoice.dian_status = 'processing'

                invoice.save()

                # Descargar documento
                self.stdout.write('📥 Descargando documento...')
                success, content = api_client.download_invoice(response.cufe, 'xml')
                if success:
                    self.stdout.write(self.style.SUCCESS('✅ Documento descargado exitosamente'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Error descargando documento'))

            else:
                self.stdout.write(self.style.ERROR('❌ Error enviando factura:'))
                for error in response.errors:
                    self.stdout.write(self.style.ERROR(f'   - {error}'))

                invoice.dian_status = 'send_failed'
                invoice.save()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en simulación DIAN: {str(e)}'))
            # Obtener taller de prueba
            workshop = Workshop.objects.first()
            if not workshop:
                self.stdout.write(self.style.ERROR('No hay talleres registrados'))
                return

            # Obtener o crear cliente de prueba
            customer, created = Customer.objects.get_or_create(
                workshop=workshop,
                document_number='123456789',
                defaults={
                    'first_name': 'Juan',
                    'last_name': 'Pérez',
                    'document_type': 'cc',
                    'email': 'juan@example.com',
                    'phone': '3001234567',
                    'address': 'Calle 123 #45-67',
                    'city': 'Bogotá',
                    'department': 'Cundinamarca'
                }
            )

            # Obtener o crear producto de prueba
            part, created = Part.objects.get_or_create(
                workshop=workshop,
                name='Filtro de aceite',
                defaults={
                    'description': 'Filtro de aceite para motocicleta',
                    'part_number': 'FLT-001',
                    'category': 'filtros',
                    'stock_quantity': 50,
                    'unit_cost': 15000,
                    'sale_price': 25000,
                    'is_taxable': True
                }
            )

            # Crear factura electrónica de prueba
            invoice = ElectronicInvoice.objects.create(
                workshop=workshop,
                customer=customer,
                dian_resolution=workshop.dian_resolutions.first(),
                issue_date=timezone.now(),
                issue_time=timezone.now().time(),
                due_date=timezone.now().date() + timezone.timedelta(days=30),

                # Información del taller
                workshop_nit=workshop.nit or '2022516216',
                workshop_name=workshop.name,
                workshop_address=workshop.address or 'Dirección del taller',
                workshop_city=workshop.city or 'Bogotá',
                workshop_department=workshop.department or 'Cundinamarca',
                workshop_phone=workshop.phone,
                workshop_email=workshop.email,

                # Información del cliente
                customer_name=customer.full_name,
                customer_document_type=customer.document_type,
                customer_document=customer.document_number,
                customer_address=customer.full_address,
                customer_city=customer.city,
                customer_department=customer.department,
                customer_phone=customer.phone,
                customer_email=customer.email,

                # Totales
                subtotal=25000,
                discount=0,
                tax_rate=19,
                tax_amount=4750,
                total=29750,

                # Estado
                dian_status='draft',
                payment_status='pending',
                payment_method='cash',
                notes='Factura de prueba para validación XML DIAN'
            )

            # Crear detalle de factura
            detail = ElectronicInvoiceDetail.objects.create(
                electronic_invoice=invoice,
                part=part,
                description=f'{part.name} - {part.description}',
                part_number=part.part_number,
                quantity=1,
                unit_price=25000,
                discount=0,
                tax_rate=19
            )

            self.stdout.write(self.style.SUCCESS(f'Factura electrónica creada: {invoice.invoice_number}'))

            # Generar XML (sin pretty print para evitar problemas de namespaces)
            xml_generator = DianXmlGenerator(invoice)
            xml_content = xml_generator.get_xml_string(pretty_print=False)

            # Guardar XML en la factura
            invoice.xml_content = xml_content
            invoice.save()

            self.stdout.write(self.style.SUCCESS('XML generado exitosamente'))

            # Mostrar primeras líneas del XML para debug
            lines = xml_content.split('\n')
            self.stdout.write('Primeras líneas del XML generado:')
            for i, line in enumerate(lines[:5]):
                self.stdout.write(f'  {i+1}: {line[:100]}...')

            # Validar XML con validador básico
            basic_validator = DianXmlValidator(xml_content)
            basic_valid = basic_validator.validate_basic_structure()

            # Validar XML con Schematron
            schematron_validator = DianSchematronValidator(xml_content)
            schematron_valid = schematron_validator.validate_invoice()

            # Resultados de validación
            self.stdout.write('\n=== RESULTADOS DE VALIDACION ===')

            if basic_valid:
                self.stdout.write(self.style.SUCCESS('✅ Validacion XML basica: PASO'))
            else:
                self.stdout.write(self.style.ERROR('❌ Validacion XML basica: FALLO'))
                for error in basic_validator.get_validation_errors():
                    self.stdout.write(self.style.ERROR(f'   - {error}'))

            if schematron_valid:
                self.stdout.write(self.style.SUCCESS('✅ Validacion Schematron DIAN: PASO'))
            else:
                self.stdout.write(self.style.ERROR('❌ Validacion Schematron DIAN: FALLO'))
                for error in schematron_validator.get_validation_errors():
                    self.stdout.write(self.style.ERROR(f'   - {error}'))

            # Mostrar warnings si existen
            warnings = schematron_validator.get_validation_warnings()
            if warnings:
                self.stdout.write(self.style.WARNING('⚠️  Advertencias:'))
                for warning in warnings:
                    self.stdout.write(self.style.WARNING(f'   - {warning}'))

            # Validación general
            overall_valid = basic_valid and schematron_valid
            if overall_valid:
                self.stdout.write(self.style.SUCCESS('🎉 VALIDACION COMPLETA: TODAS LAS PRUEBAS PASARON'))

                # Si validación pasa, intentar envío simulado a DIAN
                self.stdout.write('\n🚀 PRUEBA DE ENVÍO A DIAN (SIMULADO):')
                self._test_dian_submission(xml_content, invoice)

            else:
                self.stdout.write(self.style.ERROR('❌ VALIDACION COMPLETA: ERRORES DETECTADOS'))

            # Mostrar información de la factura
            self.stdout.write('\n' + '='*50)
            self.stdout.write('INFORMACIÓN DE LA FACTURA DE PRUEBA')
            self.stdout.write('='*50)
            self.stdout.write(f'Número: {invoice.invoice_number}')
            self.stdout.write(f'CUDE: {invoice.cude}')
            self.stdout.write(f'Fecha: {invoice.issue_date.strftime("%Y-%m-%d %H:%M:%S")}')
            self.stdout.write(f'Cliente: {invoice.customer_name}')
            self.stdout.write(f'Subtotal: ${invoice.subtotal:,.0f}')
            self.stdout.write(f'IVA (19%): ${invoice.tax_amount:,.0f}')
            self.stdout.write(f'Total: ${invoice.total:,.0f}')
            self.stdout.write(f'Estado DIAN: {invoice.get_dian_status_display()}')
            self.stdout.write('='*50)

            # Guardar XML en archivo para revisión (solo si validación básica pasa)
            if basic_valid or options['save_xml']:
                filename = f'factura_prueba_{invoice.invoice_number}.xml'
                xml_generator.save_xml_file(filename)
                self.stdout.write(self.style.SUCCESS(f'XML guardado en: {filename}'))
            else:
                self.stdout.write(self.style.WARNING('XML no guardado debido a errores de validacion'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            traceback.print_exc()

    def add_arguments(self, parser):
        """Agregar argumentos opcionales al comando"""
        parser.add_argument(
            '--environment',
            type=str,
            choices=['simulation', 'testing', 'production'],
            default='simulation',
            help='Ambiente DIAN a utilizar'
        )

        parser.add_argument(
            '--save-xml',
            action='store_true',
            help='Guardar XML generado en archivo'
        )
        """Método principal con argumentos"""
        # Usar el ambiente especificado
        env_map = {
            'simulation': DianEnvironment.SIMULATION,
            'testing': DianEnvironment.TESTING,
            'production': DianEnvironment.PRODUCTION
        }

        environment = env_map.get(options['environment'], DianEnvironment.SIMULATION)

        try:
            # Obtener taller de prueba
            workshop = Workshop.objects.first()
            if not workshop:
                self.stdout.write(self.style.ERROR('No hay talleres registrados'))
                return

            # Obtener o crear cliente de prueba
            customer, created = Customer.objects.get_or_create(
                workshop=workshop,
                document_number='123456789',
                defaults={
                    'first_name': 'Juan',
                    'last_name': 'Pérez',
                    'document_type': 'cc',
                    'email': 'juan@example.com',
                    'phone': '3001234567',
                    'address': 'Calle 123 #45-67',
                    'city': 'Bogotá',
                    'department': 'Cundinamarca'
                }
            )

            # Obtener o crear producto de prueba
            part, created = Part.objects.get_or_create(
                workshop=workshop,
                name='Filtro de aceite',
                defaults={
                    'description': 'Filtro de aceite para motocicleta',
                    'part_number': 'FLT-001',
                    'category': 'filtros',
                    'stock_quantity': 50,
                    'unit_cost': 15000,
                    'sale_price': 25000,
                    'is_taxable': True
                }
            )

            # Crear factura electrónica de prueba
            invoice = ElectronicInvoice.objects.create(
                workshop=workshop,
                customer=customer,
                dian_resolution=workshop.dian_resolutions.first(),
                issue_date=timezone.now(),
                issue_time=timezone.now().time(),
                due_date=timezone.now().date() + timezone.timedelta(days=30),

                # Información del taller
                workshop_nit=workshop.nit or '2022516216',
                workshop_name=workshop.name,
                workshop_address=workshop.address or 'Dirección del taller',
                workshop_city=workshop.city or 'Bogotá',
                workshop_department=workshop.department or 'Cundinamarca',
                workshop_phone=workshop.phone,
                workshop_email=workshop.email,

                # Información del cliente
                customer_name=customer.full_name,
                customer_document_type=customer.document_type,
                customer_document=customer.document_number,
                customer_address=customer.full_address,
                customer_city=customer.city,
                customer_department=customer.department,
                customer_phone=customer.phone,
                customer_email=customer.email,

                # Totales
                subtotal=25000,
                discount=0,
                tax_rate=19,
                tax_amount=4750,
                total=29750,

                # Estado
                dian_status='draft',
                payment_status='pending',
                payment_method='cash',
                notes='Factura de prueba para validación XML DIAN'
            )

            # Crear detalle de factura
            detail = ElectronicInvoiceDetail.objects.create(
                electronic_invoice=invoice,
                part=part,
                description=f'{part.name} - {part.description}',
                part_number=part.part_number,
                quantity=1,
                unit_price=25000,
                discount=0,
                tax_rate=19
            )

            self.stdout.write(self.style.SUCCESS(f'Factura electrónica creada: {invoice.invoice_number}'))

            # Generar XML (sin pretty print para evitar problemas de namespaces)
            xml_generator = DianXmlGenerator(invoice)
            xml_content = xml_generator.get_xml_string(pretty_print=False)

            # Guardar XML en la factura
            invoice.xml_content = xml_content
            invoice.save()

            self.stdout.write(self.style.SUCCESS('XML generado exitosamente'))

            # Mostrar primeras líneas del XML para debug
            lines = xml_content.split('\n')
            self.stdout.write('Primeras líneas del XML generado:')
            for i, line in enumerate(lines[:5]):
                self.stdout.write(f'  {i+1}: {line[:100]}...')

            # Validar XML con validador básico
            basic_validator = DianXmlValidator(xml_content)
            basic_valid = basic_validator.validate_basic_structure()

            # Validar XML con Schematron
            schematron_validator = DianSchematronValidator(xml_content)
            schematron_valid = schematron_validator.validate_invoice()

            # Resultados de validación
            self.stdout.write('\n=== RESULTADOS DE VALIDACION ===')

            if basic_valid:
                self.stdout.write(self.style.SUCCESS('✅ Validacion XML basica: PASO'))
            else:
                self.stdout.write(self.style.ERROR('❌ Validacion XML basica: FALLO'))
                for error in basic_validator.get_validation_errors():
                    self.stdout.write(self.style.ERROR(f'   - {error}'))

            if schematron_valid:
                self.stdout.write(self.style.SUCCESS('✅ Validacion Schematron DIAN: PASO'))
            else:
                self.stdout.write(self.style.ERROR('❌ Validacion Schematron DIAN: FALLO'))
                for error in schematron_validator.get_validation_errors():
                    self.stdout.write(self.style.ERROR(f'   - {error}'))

            # Mostrar warnings si existen
            warnings = schematron_validator.get_validation_warnings()
            if warnings:
                self.stdout.write(self.style.WARNING('⚠️  Advertencias:'))
                for warning in warnings:
                    self.stdout.write(self.style.WARNING(f'   - {warning}'))

            # Validación general
            overall_valid = basic_valid and schematron_valid
            if overall_valid:
                self.stdout.write(self.style.SUCCESS('🎉 VALIDACION COMPLETA: TODAS LAS PRUEBAS PASARON'))

                # Si validación pasa, intentar envío simulado a DIAN
                self.stdout.write('\n🚀 PRUEBA DE ENVÍO A DIAN (SIMULADO):')
                self._test_dian_submission(xml_content, invoice)

            else:
                self.stdout.write(self.style.ERROR('❌ VALIDACION COMPLETA: ERRORES DETECTADOS'))

            # Mostrar información de la factura
            self.stdout.write('\n' + '='*50)
            self.stdout.write('INFORMACIÓN DE LA FACTURA DE PRUEBA')
            self.stdout.write('='*50)
            self.stdout.write(f'Número: {invoice.invoice_number}')
            self.stdout.write(f'CUDE: {invoice.cude}')
            self.stdout.write(f'Fecha: {invoice.issue_date.strftime("%Y-%m-%d %H:%M:%S")}')
            self.stdout.write(f'Cliente: {invoice.customer_name}')
            self.stdout.write(f'Subtotal: ${invoice.subtotal:,.0f}')
            self.stdout.write(f'IVA (19%): ${invoice.tax_amount:,.0f}')
            self.stdout.write(f'Total: ${invoice.total:,.0f}')
            self.stdout.write(f'Estado DIAN: {invoice.get_dian_status_display()}')
            self.stdout.write('='*50)

            # Guardar XML en archivo para revisión (solo si validación básica pasa)
            if basic_valid or options['save_xml']:
                filename = f'factura_prueba_{invoice.invoice_number}.xml'
                xml_generator.save_xml_file(filename)
                self.stdout.write(self.style.SUCCESS(f'XML guardado en: {filename}'))
            else:
                self.stdout.write(self.style.WARNING('XML no guardado debido a errores de validacion'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            traceback.print_exc()
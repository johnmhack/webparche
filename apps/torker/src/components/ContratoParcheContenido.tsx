import { CONTRATO_PARCHE_VERSION } from '../lib/contrato';

/** Texto del contrato marco (versión mostrada en Torker). Reemplazar por PDF legal cuando esté listo. */
export function ContratoParcheContenido({ tallerNombre }: { tallerNombre?: string }) {
  return (
    <article className="prose-contrato space-y-4 text-sm leading-relaxed text-slate-300">
      <header className="border-b border-parche-border pb-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-cyan-400">
          Contrato de servicio · Versión {CONTRATO_PARCHE_VERSION}
        </p>
        <h2 className="mt-1 text-lg font-bold text-white">
          Acuerdo de uso de la plataforma Torker by Parche
        </h2>
        <p className="mt-2 text-xs text-slate-500">
          Entre Parche (operador de la plataforma) y el establecimiento
          {tallerNombre ? ` «${tallerNombre}»` : ' afiliado'} (el «Taller»).
        </p>
      </header>

      <section>
        <h3 className="font-semibold text-white">1. Objeto</h3>
        <p>
          Parche pone a disposición del Taller la herramienta Torker para gestionar clientes,
          agenda, inventario, órdenes de trabajo y la vinculación con moteros usuarios de la
          aplicación Parche, conforme a las funcionalidades vigentes.
        </p>
      </section>

      <section>
        <h3 className="font-semibold text-white">2. Cuenta y datos del establecimiento</h3>
        <p>
          El Taller es responsable de mantener actualizado el perfil de su establecimiento
          (nombre, dirección, contacto, NIT u otros datos que registre) y de la veracidad de la
          información. El acceso se realiza con la cuenta del propietario o representante
          autorizado.
        </p>
      </section>

      <section>
        <h3 className="font-semibold text-white">3. Datos de clientes y moteros</h3>
        <p>
          El Taller tratará los datos personales de sus clientes y, cuando aplique, de moteros
          Parche, solo para la prestación del servicio de taller y conforme a la ley aplicable
          (incluida la Ley 1581 de 2012 en Colombia). No podrá usar la plataforma para fines
          ajenos al taller ni ceder datos a terceros no autorizados.
        </p>
      </section>

      <section>
        <h3 className="font-semibold text-white">4. Órdenes, historial y evidencia</h3>
        <p>
          Las órdenes cerradas con evidencia (descripción y fotos) pueden quedar registradas en
          el historial de la moto cuando exista vínculo Parche. Esa información se considera
          verificada por el Taller; errores materiales deben reportarse a soporte Parche.
        </p>
      </section>

      <section>
        <h3 className="font-semibold text-white">5. Disponibilidad y cambios</h3>
        <p>
          Parche podrá mejorar, limitar o modificar funcionalidades de Torker con aviso razonable.
          No garantiza disponibilidad ininterrumpida. El Taller puede dejar de usar el servicio
          en cualquier momento; el cese no libera obligaciones ya adquiridas sobre datos o
          registros generados.
        </p>
      </section>

      <section>
        <h3 className="font-semibold text-white">6. Propiedad intelectual</h3>
        <p>
          La plataforma, marcas y software de Parche/Torker son de Parche o sus licenciantes. El
          Taller obtiene una licencia limitada, no exclusiva e intransferible de uso durante la
          vigencia del servicio.
        </p>
      </section>

      <section>
        <h3 className="font-semibold text-white">7. Aceptación</h3>
        <p>
          Al marcar «Acepto el contrato» en Torker, el representante del Taller declara haber
          leído este documento (versión {CONTRATO_PARCHE_VERSION}) y aceptar sus términos. Parche
          podrá sustituir este texto por un PDF notarial o comercial actualizado; en ese caso se
          solicitará nueva aceptación de la versión vigente.
        </p>
      </section>

      <p className="text-xs text-slate-500">
        Documento informativo de términos de uso de la plataforma. Si Parche entrega un contrato
        firmado en PDF, ese documento prevalece sobre este resumen.
      </p>
    </article>
  );
}

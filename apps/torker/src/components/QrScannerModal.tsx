import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Html5Qrcode } from 'html5-qrcode';
import { Loader2, X } from 'lucide-react';

const SCANNER_ID = 'parche-qr-reader';

/** Extrae el código Parche del texto del QR (código puro o URL). */
export function normalizarCodigoQr(raw: string): string {
  const t = raw.trim();
  if (!t) return '';

  try {
    const u = new URL(t);
    const q = u.searchParams.get('codigo') || u.searchParams.get('c') || u.searchParams.get('data');
    if (q) return q.trim().toUpperCase();
    const parts = u.pathname.split('/').filter(Boolean);
    const last = parts[parts.length - 1];
    if (last && /^[A-Za-z0-9_-]{4,16}$/.test(last)) return last.toUpperCase();
  } catch {
    /* texto plano */
  }

  // Si el QR trae "data=XXXX" suelto
  const dataMatch = t.match(/(?:^|[?&])data=([^&]+)/i);
  if (dataMatch?.[1]) {
    try {
      return decodeURIComponent(dataMatch[1]).trim().toUpperCase();
    } catch {
      return dataMatch[1].trim().toUpperCase();
    }
  }

  return t.toUpperCase().replace(/[^A-Z0-9]/g, '');
}

async function stopScanner(scanner: Html5Qrcode | null) {
  if (!scanner) return;
  try {
    const state = scanner.getState?.();
    // 2 = SCANNING, 3 = PAUSED (html5-qrcode Html5QrcodeScannerState)
    if (state === 2 || state === 3) {
      await scanner.stop();
    }
  } catch {
    /* ya detenido */
  }
  try {
    scanner.clear();
  } catch {
    /* ignore */
  }
  const el = document.getElementById(SCANNER_ID);
  if (el) el.innerHTML = '';
}

export function QrScannerModal({
  open,
  onClose,
  onScan,
}: {
  open: boolean;
  onClose: () => void;
  onScan: (codigo: string) => void;
}) {
  const [error, setError] = useState('');
  const [starting, setStarting] = useState(false);
  const [closing, setClosing] = useState(false);
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const handledRef = useRef(false);
  const onScanRef = useRef(onScan);
  const onCloseRef = useRef(onClose);
  onScanRef.current = onScan;
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!open) return;

    handledRef.current = false;
    setError('');
    setStarting(true);
    setClosing(false);

    let cancelled = false;
    let scanner: Html5Qrcode | null = null;

    const timer = window.setTimeout(async () => {
      if (cancelled) return;
      const host = document.getElementById(SCANNER_ID);
      if (!host) {
        setStarting(false);
        setError('No se pudo iniciar el escáner');
        return;
      }

      scanner = new Html5Qrcode(SCANNER_ID, { verbose: false });
      scannerRef.current = scanner;

      try {
        await scanner.start(
          { facingMode: 'environment' },
          { fps: 8, qrbox: { width: 220, height: 220 }, aspectRatio: 1 },
          async (decoded) => {
            if (handledRef.current || cancelled) return;
            const codigo = normalizarCodigoQr(decoded);
            if (!codigo) return;

            handledRef.current = true;
            setClosing(true);
            await stopScanner(scanner);
            scannerRef.current = null;
            if (!cancelled) onScanRef.current(codigo);
          },
          () => {},
        );
        if (!cancelled) setStarting(false);
      } catch (e) {
        if (!cancelled) {
          setStarting(false);
          setError(
            e instanceof Error
              ? e.message
              : 'No se pudo abrir la cámara. Revisa permisos del navegador.',
          );
        }
      }
    }, 150);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      const s = scannerRef.current;
      scannerRef.current = null;
      void stopScanner(s);
    };
  }, [open]);

  const handleClose = async () => {
    setClosing(true);
    await stopScanner(scannerRef.current);
    scannerRef.current = null;
    onCloseRef.current();
  };

  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 z-[90] flex items-end justify-center sm:items-center p-0 sm:p-4">
      <div className="absolute inset-0 bg-black/85" onClick={() => void handleClose()} />
      <div className="relative z-10 w-full max-w-md overflow-hidden rounded-t-2xl border border-parche-border bg-slate-900 shadow-2xl sm:rounded-2xl">
        <div className="flex items-center justify-between border-b border-parche-border px-4 py-3">
          <h2 className="font-semibold text-white">Escanear código Parche</h2>
          <button
            type="button"
            className="btn-ghost p-2"
            onClick={() => void handleClose()}
            aria-label="Cerrar"
            disabled={closing}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-4">
          <p className="mb-3 text-xs text-slate-500">
            Apunta al QR de la moto en la app Parche. Al leerlo se busca automáticamente.
          </p>

          <div className="relative overflow-hidden rounded-xl bg-black">
            {/* Contenedor vacío: html5-qrcode inyecta el video aquí */}
            <div id={SCANNER_ID} className="min-h-[300px] w-full overflow-hidden" />
            {(starting || closing) && !error && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-slate-950/85">
                <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
                <p className="text-xs text-slate-400">
                  {closing ? 'Código leído…' : 'Abriendo cámara…'}
                </p>
              </div>
            )}
          </div>

          {error && <p className="mt-3 text-sm text-pink-400">{error}</p>}

          <button
            type="button"
            className="btn-secondary mt-4 w-full"
            onClick={() => void handleClose()}
            disabled={closing}
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}

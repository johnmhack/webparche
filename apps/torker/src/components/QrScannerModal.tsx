import { useEffect, useRef, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { Loader2, X } from 'lucide-react';

const SCANNER_ID = 'parche-qr-reader';

function normalizarCodigo(raw: string): string {
  const t = raw.trim();
  try {
    const u = new URL(t);
    const fromPath = u.pathname.split('/').filter(Boolean).pop();
    if (fromPath) return fromPath.toUpperCase();
    const q = u.searchParams.get('codigo') || u.searchParams.get('c');
    if (q) return q.toUpperCase();
  } catch {
    /* no es URL */
  }
  return t.toUpperCase().replace(/[^A-Z0-9]/g, '');
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
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const handledRef = useRef(false);

  const onScanRef = useRef(onScan);
  onScanRef.current = onScan;

  useEffect(() => {
    if (!open) return;
    handledRef.current = false;
    setError('');
    setStarting(true);

    let cancelled = false;
    const scanner = new Html5Qrcode(SCANNER_ID);
    scannerRef.current = scanner;

    (async () => {
      try {
        await scanner.start(
          { facingMode: 'environment' },
          { fps: 10, qrbox: { width: 240, height: 240 } },
          (decoded) => {
            if (handledRef.current || cancelled) return;
            const codigo = normalizarCodigo(decoded);
            if (!codigo) return;
            handledRef.current = true;
            onScanRef.current(codigo);
            void scanner.stop().catch(() => {});
          },
          () => {
            /* frame sin QR — ignorar */
          },
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
    })();

    return () => {
      cancelled = true;
      const s = scannerRef.current;
      scannerRef.current = null;
      if (s) {
        s.stop()
          .then(() => s.clear())
          .catch(() => {});
      }
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-end justify-center sm:items-center p-0 sm:p-4">
      <div className="absolute inset-0 bg-black/80" onClick={onClose} />
      <div className="relative w-full max-w-md overflow-hidden rounded-t-2xl border border-parche-border bg-slate-900 shadow-2xl sm:rounded-2xl">
        <div className="flex items-center justify-between border-b border-parche-border px-4 py-3">
          <h2 className="font-semibold text-white">Escanear código Parche</h2>
          <button type="button" className="btn-ghost p-2" onClick={onClose} aria-label="Cerrar">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-4">
          <p className="mb-3 text-xs text-slate-500">
            Apunta la cámara al QR de la app del motero. Usa HTTPS o localhost para permisos.
          </p>

          <div className="relative overflow-hidden rounded-xl bg-black">
            <div id={SCANNER_ID} className="min-h-[280px] w-full" />
            {starting && !error && (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80">
                <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
              </div>
            )}
          </div>

          {error && <p className="mt-3 text-sm text-pink-400">{error}</p>}

          <button type="button" className="btn-secondary mt-4 w-full" onClick={onClose}>
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}

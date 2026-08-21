import { useEffect, useState } from 'react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';

/** Miniaturas + lightbox en la misma pantalla (sin abrir pestaña). */
export function FotosHistorial({ urls }: { urls: string[] }) {
  const [index, setIndex] = useState<number | null>(null);

  useEffect(() => {
    if (index === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIndex(null);
      if (e.key === 'ArrowLeft') setIndex((i) => (i == null ? i : (i - 1 + urls.length) % urls.length));
      if (e.key === 'ArrowRight') setIndex((i) => (i == null ? i : (i + 1) % urls.length));
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [index, urls.length]);

  if (!urls.length) return null;

  return (
    <>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {urls.map((url, i) => (
          <button
            key={url}
            type="button"
            onClick={() => setIndex(i)}
            className="block overflow-hidden rounded-md border border-white/10 transition hover:border-cyan-400/50"
          >
            <img src={url} alt="" className="h-14 w-14 object-cover" />
          </button>
        ))}
      </div>

      {index !== null && (
        <div
          className="fixed inset-0 z-[80] flex items-center justify-center bg-black/85 p-4"
          onClick={() => setIndex(null)}
        >
          <button
            type="button"
            className="absolute right-4 top-4 rounded-full bg-white/10 p-2 text-white hover:bg-white/20"
            onClick={() => setIndex(null)}
            aria-label="Cerrar"
          >
            <X className="h-5 w-5" />
          </button>

          {urls.length > 1 && (
            <>
              <button
                type="button"
                className="absolute left-3 rounded-full bg-white/10 p-2 text-white hover:bg-white/20 sm:left-6"
                onClick={(e) => {
                  e.stopPropagation();
                  setIndex((i) => (i == null ? 0 : (i - 1 + urls.length) % urls.length));
                }}
                aria-label="Anterior"
              >
                <ChevronLeft className="h-6 w-6" />
              </button>
              <button
                type="button"
                className="absolute right-3 rounded-full bg-white/10 p-2 text-white hover:bg-white/20 sm:right-6"
                onClick={(e) => {
                  e.stopPropagation();
                  setIndex((i) => (i == null ? 0 : (i + 1) % urls.length));
                }}
                aria-label="Siguiente"
              >
                <ChevronRight className="h-6 w-6" />
              </button>
            </>
          )}

          <img
            src={urls[index]}
            alt=""
            className="max-h-[85vh] max-w-full rounded-lg object-contain shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
          <p className="absolute bottom-4 text-xs text-slate-400">
            {index + 1} / {urls.length} · Esc para cerrar
          </p>
        </div>
      )}
    </>
  );
}

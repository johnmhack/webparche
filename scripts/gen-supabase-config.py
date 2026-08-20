"""Genera config Supabase para local y Netlify.

- assets/js/supabase-config.js  → local (gitignore)
- assets/js/supabase-runtime.js → deploy (sí se publica en Netlify)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def main() -> int:
    parche_env = Path(r'C:\Users\USUARIO\Desktop\parche2\.env')
    parche = read_env(parche_env)
    torker = read_env(ROOT / 'torker-backend' / '.env')

    url = (
        os.environ.get('SUPABASE_URL')
        or os.environ.get('EXPO_PUBLIC_SUPABASE_URL')
        or parche.get('EXPO_PUBLIC_SUPABASE_URL')
        or torker.get('SUPABASE_URL', '')
    )
    key = (
        os.environ.get('SUPABASE_ANON_KEY')
        or os.environ.get('EXPO_PUBLIC_SUPABASE_ANON_KEY')
        or parche.get('EXPO_PUBLIC_SUPABASE_ANON_KEY', '')
        or torker.get('SUPABASE_ANON_KEY', '')
    )

    if not url or not key:
        print('MISSING: define SUPABASE_URL y SUPABASE_ANON_KEY', file=sys.stderr)
        print('Netlify → Site configuration → Environment variables', file=sys.stderr)
        return 1

    url = url.rstrip('/').replace('/rest/v1', '')
    content = (
        f"window.SUPABASE_URL = '{url}';\n"
        f"window.SUPABASE_ANON_KEY = '{key}';\n"
    )

    out_dir = ROOT / 'assets' / 'js'
    out_dir.mkdir(parents=True, exist_ok=True)

    # Local (gitignore) + Netlify (publicado)
    for name in ('supabase-config.js', 'supabase-runtime.js'):
        path = out_dir / name
        path.write_text(content, encoding='utf-8')
        print(f'OK -> {path}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

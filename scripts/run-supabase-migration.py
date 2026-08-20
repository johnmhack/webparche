#!/usr/bin/env python3
"""Ejecuta la migración clientes/citas en Supabase vía conexión Postgres directa.

Uso:
  set SUPABASE_DB_URL=postgresql://postgres.[ref]:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
  python scripts/run-supabase-migration.py

Obtén la URL en Supabase → Project Settings → Database → Connection string (URI).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

MIGRATION = Path(__file__).resolve().parents[1] / 'docs' / 'supabase' / '001_clientes_citas.sql'


def main() -> int:
    db_url = os.environ.get('SUPABASE_DB_URL') or os.environ.get('DATABASE_URL')
    if not db_url or not db_url.startswith('postgres'):
        print('Falta SUPABASE_DB_URL (connection string Postgres de Supabase).')
        print('Alternativa: copia el SQL en docs/supabase/001_clientes_citas.sql')
        print('y ejecútalo en Supabase → SQL Editor.')
        return 1

    try:
        import psycopg2
    except ImportError:
        print('Instala psycopg2-binary: pip install psycopg2-binary')
        return 1

    sql = MIGRATION.read_text(encoding='utf-8')
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        print('Migración aplicada:', MIGRATION.name)
    finally:
        conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())

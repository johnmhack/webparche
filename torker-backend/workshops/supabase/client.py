from functools import lru_cache

from decouple import config
from supabase import Client, create_client


def _normalize_supabase_url(url: str) -> str:
    url = url.strip().rstrip('/')
    if url.endswith('/rest/v1'):
        url = url[:-len('/rest/v1')].rstrip('/')
    return url


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    url = _normalize_supabase_url(config('SUPABASE_URL'))
    key = config('SUPABASE_SERVICE_ROLE_KEY')
    return create_client(url, key)


def supabase_configurado() -> bool:
    url = config('SUPABASE_URL', default='')
    key = config('SUPABASE_SERVICE_ROLE_KEY', default='')
    return bool(url and key)

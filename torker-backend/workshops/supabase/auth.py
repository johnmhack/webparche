import httpx
from decouple import config

from .client import _normalize_supabase_url, supabase_configurado


def propietario_id_desde_request(request) -> str | None:
    header = request.headers.get('X-Propietario-Id') or request.data.get('propietario_id')
    if header:
        return str(header).strip()

    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return propietario_id_desde_token(auth[7:].strip())
    return None


def propietario_id_desde_token(token: str) -> str | None:
    if not token or not supabase_configurado():
        return None

    url = _normalize_supabase_url(config('SUPABASE_URL')) + '/auth/v1/user'
    api_key = config('SUPABASE_ANON_KEY', default='') or config('SUPABASE_SERVICE_ROLE_KEY')

    for apikey in (api_key, config('SUPABASE_SERVICE_ROLE_KEY')):
        if not apikey:
            continue
        try:
            resp = httpx.get(
                url,
                headers={'Authorization': f'Bearer {token}', 'apikey': apikey},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json().get('id')
        except httpx.HTTPError:
            continue
    return None

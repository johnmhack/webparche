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


parche = read_env(Path(r'C:\Users\USUARIO\Desktop\parche2\.env'))
torker = read_env(ROOT / 'torker-backend' / '.env')
url = parche.get('EXPO_PUBLIC_SUPABASE_URL') or torker.get('SUPABASE_URL', '')
key = parche.get('EXPO_PUBLIC_SUPABASE_ANON_KEY', '')
out = ROOT / 'assets' / 'js' / 'supabase-config.js'
if url and key:
    out.write_text(
        f"window.SUPABASE_URL = '{url.rstrip('/').replace('/rest/v1', '')}';\n"
        f"window.SUPABASE_ANON_KEY = '{key}';\n",
        encoding='utf-8',
    )
    env_file = ROOT / 'torker-backend' / '.env'
    if env_file.exists():
        text = env_file.read_text(encoding='utf-8')
        if 'SUPABASE_ANON_KEY' not in text:
            env_file.write_text(text.rstrip() + f'\nSUPABASE_ANON_KEY={key}\n', encoding='utf-8')
    print('OK')
else:
    print('MISSING')

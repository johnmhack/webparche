const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL || '').replace(/\/$/, '');
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

export function getSupabaseUrl(): string {
  return supabaseUrl.replace(/\/rest\/v1\/?$/, '');
}

export function getSupabaseAnonKey(): string {
  return supabaseAnonKey;
}

export function supabaseConfigured(): boolean {
  return Boolean(supabaseUrl && supabaseAnonKey);
}

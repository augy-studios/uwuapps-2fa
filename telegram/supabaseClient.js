import { createClient } from '@supabase/supabase-js';
import { SUPABASE_URL, SUPABASE_SERVICE_KEY } from './config.js';

let _client = null;

export function getSupabase() {
  if (!_client) _client = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);
  return _client;
}

export async function findUwuUserByIdentifier(identifier) {
  const sb = getSupabase();
  const id = identifier.trim();

  let { data } = await sb
    .from('uwu_users')
    .select('id, username, email, display_name, avatar_url')
    .ilike('username', id)
    .limit(1);

  if (data?.length) return data[0];

  ({ data } = await sb
    .from('uwu_users')
    .select('id, username, email, display_name, avatar_url')
    .ilike('email', id)
    .limit(1));

  return data?.length ? data[0] : null;
}

export async function findUwuUserById(userId) {
  const { data } = await getSupabase()
    .from('uwu_users')
    .select('id, username, email, display_name, avatar_url')
    .eq('id', userId)
    .limit(1);
  return data?.length ? data[0] : null;
}

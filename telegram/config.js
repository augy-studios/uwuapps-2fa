import 'dotenv/config';

const required = (name) => {
  const val = process.env[name];
  if (!val) throw new Error(`Missing required env var: ${name}`);
  return val;
};

export const BOT_TOKEN = required('BOT_TOKEN');
export const SUPABASE_URL = required('SUPABASE_URL');
export const SUPABASE_SERVICE_KEY = required('SUPABASE_SERVICE_KEY');
export const TOKEN_EXPIRY_SECONDS = parseInt(process.env.TOKEN_EXPIRY_SECONDS || '300', 10);

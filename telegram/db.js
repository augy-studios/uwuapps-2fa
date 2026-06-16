import { getSupabase } from './supabaseClient.js';

const nowIso = () => new Date().toISOString();
const expiryIso = (s) => new Date(Date.now() + s * 1000).toISOString();

// ── Link helpers ──────────────────────────────────────────────────────────────

export async function getLinkByTelegram(telegramId) {
  const { data } = await getSupabase()
    .from('uwutele_links')
    .select('*')
    .eq('telegram_id', telegramId)
    .limit(1);
  return data?.[0] ?? null;
}

export async function getLinkByUwuUser(uwuUserId) {
  const { data } = await getSupabase()
    .from('uwutele_links')
    .select('*')
    .eq('uwu_user_id', uwuUserId)
    .limit(1);
  return data?.[0] ?? null;
}

export async function upsertLink({ telegramId, telegramUsername, uwuUserId, uwuUsername, uwuEmail, uwuDisplayName }) {
  await getSupabase()
    .from('uwutele_links')
    .upsert({
      telegram_id: telegramId,
      telegram_username: telegramUsername,
      uwu_user_id: uwuUserId,
      uwu_username: uwuUsername,
      uwu_email: uwuEmail,
      uwu_display_name: uwuDisplayName,
      linked_at: nowIso(),
    }, { onConflict: 'telegram_id' });
}

export async function deleteLink(telegramId) {
  await getSupabase()
    .from('uwutele_links')
    .delete()
    .eq('telegram_id', telegramId);
}

// ── Token helpers (Flow A — deep link) ───────────────────────────────────────

export async function insertToken({ token, uwuUserId, appId, appLabel, expirySeconds }) {
  await getSupabase()
    .from('uwutele_tokens')
    .insert({
      token,
      uwu_user_id: uwuUserId,
      app_id: appId,
      app_label: appLabel,
      expires_at: expiryIso(expirySeconds),
    });
}

export async function getValidToken(token) {
  const { data } = await getSupabase()
    .from('uwutele_tokens')
    .select('*')
    .eq('token', token)
    .eq('used', false)
    .gt('expires_at', nowIso())
    .limit(1);
  return data?.[0] ?? null;
}

export async function markTokenUsed(token) {
  await getSupabase()
    .from('uwutele_tokens')
    .update({ used: true, used_at: nowIso() })
    .eq('token', token);
}

export async function purgeExpiredTokens() {
  await getSupabase()
    .from('uwutele_tokens')
    .delete()
    .eq('used', false)
    .lt('expires_at', nowIso());
}

// ── OTP helpers (Flow B — bot-initiated) ──────────────────────────────────────

export async function insertOtp({ otp, telegramId, uwuUserId, appId, expirySeconds }) {
  await getSupabase()
    .from('uwutele_otps')
    .insert({
      otp,
      telegram_id: telegramId,
      uwu_user_id: uwuUserId,
      app_id: appId,
      expires_at: expiryIso(expirySeconds),
    });
}

export async function getValidOtp(otp) {
  const { data } = await getSupabase()
    .from('uwutele_otps')
    .select('*')
    .eq('otp', otp)
    .eq('used', false)
    .gt('expires_at', nowIso())
    .limit(1);
  return data?.[0] ?? null;
}

export async function getActiveOtpForUser(telegramId) {
  const { data } = await getSupabase()
    .from('uwutele_otps')
    .select('*')
    .eq('telegram_id', telegramId)
    .eq('used', false)
    .gt('expires_at', nowIso())
    .order('created_at', { ascending: false })
    .limit(1);
  return data?.[0] ?? null;
}

export async function markOtpUsed(otp) {
  await getSupabase()
    .from('uwutele_otps')
    .update({ used: true, used_at: nowIso() })
    .eq('otp', otp);
}

export async function purgeExpiredOtps() {
  await getSupabase()
    .from('uwutele_otps')
    .delete()
    .eq('used', false)
    .lt('expires_at', nowIso());
}

// ── Session helpers ───────────────────────────────────────────────────────────

export async function recordSession({ token, telegramId, uwuUserId, appId }) {
  await getSupabase()
    .from('uwutele_sessions')
    .insert({ token, telegram_id: telegramId, uwu_user_id: uwuUserId, app_id: appId });
}

// ── Link state helpers ────────────────────────────────────────────────────────

export async function setLinkState(telegramId, step, identifier = null) {
  await getSupabase()
    .from('uwutele_link_state')
    .upsert(
      { telegram_id: telegramId, step, identifier, updated_at: nowIso() },
      { onConflict: 'telegram_id' }
    );
}

export async function getLinkState(telegramId) {
  const { data } = await getSupabase()
    .from('uwutele_link_state')
    .select('*')
    .eq('telegram_id', telegramId)
    .limit(1);
  return data?.[0] ?? null;
}

export async function clearLinkState(telegramId) {
  await getSupabase()
    .from('uwutele_link_state')
    .delete()
    .eq('telegram_id', telegramId);
}

// ── Button persistence helpers ────────────────────────────────────────────────

export async function persistButton(messageId, chatId, buttonData, handler) {
  await getSupabase()
    .from('uwutele_buttons')
    .upsert(
      { message_id: String(messageId), chat_id: chatId, button_data: buttonData, handler },
      { onConflict: 'message_id,chat_id,button_data' }
    );
}

export async function getButtonHandler(messageId, chatId, buttonData) {
  const { data } = await getSupabase()
    .from('uwutele_buttons')
    .select('handler')
    .eq('message_id', String(messageId))
    .eq('chat_id', chatId)
    .eq('button_data', buttonData)
    .limit(1);
  return data?.[0]?.handler ?? null;
}

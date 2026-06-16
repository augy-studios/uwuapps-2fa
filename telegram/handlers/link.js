import {
  getLinkByTelegram, getLinkByUwuUser, upsertLink,
  setLinkState, getLinkState, clearLinkState,
} from '../db.js';
import { findUwuUserByIdentifier } from '../supabaseClient.js';

const STEP_WAITING_IDENTIFIER = 'waiting_identifier';

export async function linkHandler(ctx) {
  const user = ctx.from;
  const existing = await getLinkByTelegram(user.id);

  if (existing) {
    const display = existing.uwu_display_name || existing.uwu_username;
    await ctx.reply(
      `✅ Your Telegram is already linked to UwU Apps.\n\n` +
      `👤 Account: ${display} (@${existing.uwu_username})\n` +
      `📧 Email: ${existing.uwu_email}\n\n` +
      'Use /unlink if you want to remove this link.'
    );
    return;
  }

  await setLinkState(user.id, STEP_WAITING_IDENTIFIER);
  await ctx.reply(
    "🔗 Let's link your Telegram to your UwU Apps account.\n\n" +
    'Please send your UwU Apps username or email address:'
  );
}

export async function linkStepHandler(ctx) {
  const user = ctx.from;
  const state = await getLinkState(user.id);

  if (!state || state.step !== STEP_WAITING_IDENTIFIER) return;

  const identifier = ctx.message.text.trim();
  if (!identifier) {
    await ctx.reply('Please send your UwU Apps username or email address.');
    return;
  }

  const uwuUser = await findUwuUserByIdentifier(identifier);
  if (!uwuUser) {
    await ctx.reply(
      '❌ No UwU Apps account found with that username or email.\n\n' +
      'Please check and try again, or send /link to restart.'
    );
    return;
  }

  const existingUwuLink = await getLinkByUwuUser(uwuUser.id);
  if (existingUwuLink && existingUwuLink.telegram_id !== user.id) {
    await clearLinkState(user.id);
    await ctx.reply(
      '⚠️ That UwU Apps account is already linked to a different Telegram account.\n\n' +
      'Each UwU Apps account can only be linked to one Telegram account.\n' +
      'Please use the correct Telegram account, or contact support.'
    );
    return;
  }

  await upsertLink({
    telegramId: user.id,
    telegramUsername: user.username ?? '',
    uwuUserId: uwuUser.id,
    uwuUsername: uwuUser.username,
    uwuEmail: uwuUser.email,
    uwuDisplayName: uwuUser.display_name ?? '',
  });
  await clearLinkState(user.id);

  const display = uwuUser.display_name || uwuUser.username;
  await ctx.reply(
    `🎉 Linked successfully!\n\n` +
    `👤 Account: ${display} (@${uwuUser.username})\n` +
    `📧 Email: ${uwuUser.email}\n\n` +
    'You can now use "Login with Telegram" on any UwU App.\n' +
    'Use /unlink to remove this link at any time.'
  );
}

import { getLinkByTelegram, upsertLink } from '../db.js';
import { findUwuUserById } from '../supabaseClient.js';

export async function statusHandler(ctx) {
  const user = ctx.from;
  const link = await getLinkByTelegram(user.id);

  if (!link) {
    await ctx.reply(
      '🔗 Status: Not linked\n\n' +
      'Your Telegram account is not linked to any UwU Apps account.\n' +
      'Use /link to connect your account.'
    );
    return;
  }

  const uwuUser = await findUwuUserById(link.uwu_user_id);
  if (uwuUser) {
    await upsertLink({
      telegramId: user.id,
      telegramUsername: user.username ?? '',
      uwuUserId: uwuUser.id,
      uwuUsername: uwuUser.username,
      uwuEmail: uwuUser.email,
      uwuDisplayName: uwuUser.display_name ?? '',
    });
  }

  const display = uwuUser?.display_name || uwuUser?.username || link.uwu_display_name || link.uwu_username;
  const username = uwuUser?.username ?? link.uwu_username;
  const email = uwuUser?.email ?? link.uwu_email;
  const linkedAt = new Date(link.linked_at).toUTCString();

  await ctx.reply(
    `✅ Status: Linked\n\n` +
    `👤 Account: ${display} (@${username})\n` +
    `📧 Email: ${email}\n` +
    `🔗 Linked: ${linkedAt}\n\n` +
    'Use /unlink to remove this link.'
  );
}

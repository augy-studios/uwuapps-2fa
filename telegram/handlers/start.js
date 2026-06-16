import {
  purgeExpiredTokens, getValidToken, markTokenUsed, recordSession,
  getLinkByTelegram, getLinkByUwuUser, upsertLink,
} from '../db.js';
import { findUwuUserById } from '../supabaseClient.js';

export async function startHandler(ctx) {
  const user = ctx.from;
  const tokenStr = (ctx.match || '').trim();

  if (!tokenStr) {
    await ctx.reply(
      `👋 Hi ${user.first_name}!\n\n` +
      'I handle Telegram-based login for UwU Apps.\n\n' +
      '📌 Commands:\n' +
      '  /start — Process a login request (usually opened automatically)\n' +
      '  /login — Get a one-time login code to enter in a UwU App\n' +
      '  /link — Link your Telegram to your UwU Apps account\n' +
      '  /unlink — Remove the link\n' +
      '  /status — Check your link status\n' +
      '  /help — More information\n\n' +
      'To log in to a UwU App via Telegram, click the "Login with Telegram" button inside the app.'
    );
    return;
  }

  await purgeExpiredTokens();
  const tokenRow = await getValidToken(tokenStr);

  if (!tokenRow) {
    await ctx.reply('❌ This login link is invalid or has expired.\n\nPlease request a new login link from the app.');
    return;
  }

  const { uwu_user_id: uwuUserId, app_label: appLabel, app_id: appId } = tokenRow;

  const uwuUser = await findUwuUserById(uwuUserId);
  if (!uwuUser) {
    await ctx.reply('❌ The UwU Apps account linked to this login request no longer exists.\n\nPlease contact support.');
    return;
  }

  const tgLink = await getLinkByTelegram(user.id);

  if (tgLink) {
    if (tgLink.uwu_user_id !== uwuUserId) {
      await ctx.reply(
        `⚠️ Your Telegram account is currently linked to a different UwU Apps account (@${tgLink.uwu_username}).\n\n` +
        'If you want to log in as a different user, please /unlink first.'
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
    await markTokenUsed(tokenStr);
    await recordSession({ token: tokenStr, telegramId: user.id, uwuUserId, appId });

    const display = uwuUser.display_name || uwuUser.username;
    await ctx.reply(
      `✅ Login approved!\n\n` +
      `🌐 App: ${appLabel}\n` +
      `👤 Logged in as: ${display} (@${uwuUser.username})\n\n` +
      'You can return to the app — you are now logged in.'
    );
    return;
  }

  const uwuLink = await getLinkByUwuUser(uwuUserId);
  if (uwuLink && uwuLink.telegram_id !== user.id) {
    await ctx.reply(
      '⚠️ This UwU Apps account is already linked to a different Telegram account.\n\n' +
      'Each UwU Apps account can only be linked to one Telegram account at a time.\n' +
      'Please use the Telegram account that was originally linked, or unlink it first.'
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
  await markTokenUsed(tokenStr);
  await recordSession({ token: tokenStr, telegramId: user.id, uwuUserId, appId });

  const display = uwuUser.display_name || uwuUser.username;
  await ctx.reply(
    `🎉 Your Telegram account has been linked to UwU Apps and your login is approved!\n\n` +
    `🌐 App: ${appLabel}\n` +
    `👤 Logged in as: ${display} (@${uwuUser.username})\n\n` +
    'You can return to the app — you are now logged in.\n\n' +
    'ℹ️ Future logins from any UwU App will be approved automatically via this chat.'
  );
}

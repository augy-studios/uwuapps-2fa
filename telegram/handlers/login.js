import { randomInt } from 'crypto';
import { InlineKeyboard } from 'grammy';
import {
  getLinkByTelegram, insertOtp, getActiveOtpForUser,
  purgeExpiredOtps, markOtpUsed, persistButton,
} from '../db.js';
import { TOKEN_EXPIRY_SECONDS } from '../config.js';

const generateOtp = () => String(randomInt(0, 1_000_000)).padStart(6, '0');

export async function loginHandler(ctx) {
  const user = ctx.from;
  const link = await getLinkByTelegram(user.id);

  if (!link) {
    await ctx.reply(
      '⚠️ Your Telegram is not linked to any UwU Apps account yet.\n\n' +
      'Use /link to connect your account first, then use /login to get a login code.'
    );
    return;
  }

  await purgeExpiredOtps();

  const existing = await getActiveOtpForUser(user.id);
  const keyboard = new InlineKeyboard().text('🔄 Generate new code', 'login_refresh');

  if (existing) {
    const msg = await ctx.reply(
      `🔑 You already have an active login code:\n\n` +
      `<code>${existing.otp}</code>\n\n` +
      `Enter this code in the UwU App login form.\n` +
      `It expires in ${TOKEN_EXPIRY_SECONDS / 60} minutes and is single-use.\n\n` +
      'Need a fresh code instead?',
      { parse_mode: 'HTML', reply_markup: keyboard }
    );
    await persistButton(msg.message_id, ctx.chat.id, 'login_refresh', 'login');
    return;
  }

  const appId = (ctx.match || '').trim() || 'uwuapps';
  const otp = generateOtp();

  await insertOtp({
    otp,
    telegramId: user.id,
    uwuUserId: link.uwu_user_id,
    appId,
    expirySeconds: TOKEN_EXPIRY_SECONDS,
  });

  const display = link.uwu_display_name || link.uwu_username;
  const msg = await ctx.reply(
    `🔑 Your login code:\n\n` +
    `<code>${otp}</code>\n\n` +
    `👤 Account: ${display} (@${link.uwu_username})\n\n` +
    `Enter this code in the UwU App login form.\n` +
    `It expires in ${TOKEN_EXPIRY_SECONDS / 60} minutes and is single-use.`,
    { parse_mode: 'HTML', reply_markup: keyboard }
  );
  await persistButton(msg.message_id, ctx.chat.id, 'login_refresh', 'login');
}

export async function loginRefreshHandler(ctx) {
  await ctx.answerCallbackQuery();
  const user = ctx.from;

  const link = await getLinkByTelegram(user.id);
  if (!link) {
    await ctx.editMessageText('⚠️ Your account is no longer linked. Use /link to reconnect.');
    return;
  }

  await purgeExpiredOtps();

  const existing = await getActiveOtpForUser(user.id);
  if (existing) await markOtpUsed(existing.otp);

  const otp = generateOtp();
  await insertOtp({
    otp,
    telegramId: user.id,
    uwuUserId: link.uwu_user_id,
    appId: 'uwuapps',
    expirySeconds: TOKEN_EXPIRY_SECONDS,
  });

  const display = link.uwu_display_name || link.uwu_username;
  const keyboard = new InlineKeyboard().text('🔄 Generate new code', 'login_refresh');

  await ctx.editMessageText(
    `🔑 Your new login code:\n\n` +
    `<code>${otp}</code>\n\n` +
    `👤 Account: ${display} (@${link.uwu_username})\n\n` +
    `Enter this code in the UwU App login form.\n` +
    `It expires in ${TOKEN_EXPIRY_SECONDS / 60} minutes and is single-use.`,
    { parse_mode: 'HTML', reply_markup: keyboard }
  );

  const msg = ctx.callbackQuery.message;
  await persistButton(msg.message_id, msg.chat.id, 'login_refresh', 'login');
}

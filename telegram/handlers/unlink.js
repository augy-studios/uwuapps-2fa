import { InlineKeyboard } from 'grammy';
import { getLinkByTelegram, deleteLink, clearLinkState, persistButton } from '../db.js';

export async function unlinkHandler(ctx) {
  const user = ctx.from;
  const existing = await getLinkByTelegram(user.id);

  if (!existing) {
    await ctx.reply(
      'ℹ️ Your Telegram is not currently linked to any UwU Apps account.\n\nUse /link to link one.'
    );
    return;
  }

  const display = existing.uwu_display_name || existing.uwu_username;
  const keyboard = new InlineKeyboard()
    .text('✅ Yes, unlink', 'unlink_confirm')
    .text('❌ Cancel', 'unlink_cancel');

  const msg = await ctx.reply(
    `⚠️ Are you sure you want to unlink your Telegram from:\n\n` +
    `👤 ${display} (@${existing.uwu_username})\n` +
    `📧 ${existing.uwu_email}\n\n` +
    'You will need to re-link to use "Login with Telegram" again.',
    { reply_markup: keyboard }
  );

  for (const data of ['unlink_confirm', 'unlink_cancel']) {
    await persistButton(msg.message_id, ctx.chat.id, data, 'unlink');
  }
}

export async function unlinkConfirmHandler(ctx) {
  await ctx.answerCallbackQuery();
  const user = ctx.from;
  const data = ctx.callbackQuery.data;

  if (data === 'unlink_cancel') {
    await ctx.editMessageText('↩️ Unlink cancelled. Your account remains linked.');
    return;
  }

  if (data === 'unlink_confirm') {
    const existing = await getLinkByTelegram(user.id);
    if (!existing) {
      await ctx.editMessageText('ℹ️ Your Telegram was not linked to any account (nothing to unlink).');
      return;
    }

    await deleteLink(user.id);
    await clearLinkState(user.id);
    await ctx.editMessageText(
      '🔓 Your Telegram has been unlinked from UwU Apps.\n\nUse /link to link a new account.'
    );
  }
}

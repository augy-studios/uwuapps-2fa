import { getButtonHandler } from '../db.js';
import { unlinkConfirmHandler } from './unlink.js';
import { loginRefreshHandler } from './login.js';

const HANDLER_REGISTRY = {
  unlink: unlinkConfirmHandler,
  login: loginRefreshHandler,
};

export async function callbackHandler(ctx) {
  const { message_id: messageId, chat } = ctx.callbackQuery.message;
  const data = ctx.callbackQuery.data;

  const handlerName = await getButtonHandler(messageId, chat.id, data);

  if (handlerName && HANDLER_REGISTRY[handlerName]) {
    await HANDLER_REGISTRY[handlerName](ctx);
  } else {
    await ctx.answerCallbackQuery({ text: 'This button is no longer active.', show_alert: true });
  }
}

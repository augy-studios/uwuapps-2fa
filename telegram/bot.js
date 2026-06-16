import 'dotenv/config';
import { Bot } from 'grammy';
import { BOT_TOKEN } from './config.js';
import { startHandler } from './handlers/start.js';
import { linkHandler, linkStepHandler } from './handlers/link.js';
import { unlinkHandler, unlinkConfirmHandler } from './handlers/unlink.js';
import { statusHandler } from './handlers/status.js';
import { helpHandler } from './handlers/help.js';
import { loginHandler, loginRefreshHandler } from './handlers/login.js';
import { callbackHandler } from './handlers/callback.js';

const bot = new Bot(BOT_TOKEN);

bot.catch((err) => {
  const ctx = err.ctx;
  console.error(`Error handling update ${ctx.update.update_id}:`, err.error);
});

bot.command('start', startHandler);
bot.command('login', loginHandler);
bot.command('link', linkHandler);
bot.command('unlink', unlinkHandler);
bot.command('status', statusHandler);
bot.command('help', helpHandler);

// Specific callback patterns before the generic DB-lookup fallback
bot.callbackQuery(/^unlink_/, unlinkConfirmHandler);
bot.callbackQuery('login_refresh', loginRefreshHandler);
bot.callbackQuery(/[\s\S]*/, callbackHandler);

// Multi-step conversation text (e.g. /link flow)
bot.on('message:text', linkStepHandler);

bot.api.setMyCommands([
  { command: 'start',  description: 'Start or process a login request' },
  { command: 'login',  description: 'Get a one-time login code to enter in a UwU App' },
  { command: 'link',   description: 'Link your Telegram to your UwU Apps account' },
  { command: 'unlink', description: 'Unlink your Telegram from your UwU Apps account' },
  { command: 'status', description: 'Check your link status' },
  { command: 'help',   description: 'Show help information' },
]);

console.log('Starting UwU Apps 2FA Bot...');
bot.start({
  drop_pending_updates: true,
  onStart: (info) => console.log(`Bot @${info.username} is running`),
});
